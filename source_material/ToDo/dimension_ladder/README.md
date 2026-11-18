# The dimension ladder — what a packing in 2D becomes in 3D, 4D, …, 24D

**The short answer.** There is a chain, and it is the *laminated* chain: the hexagonal
lattice in 2D is the 3D face-centred cubic lattice's layer, FCC is D₄'s layer, D₄ is D₅'s,
and so on up through E₆, E₇, E₈ to the Leech lattice in 24 dimensions. But the chain is a
chain of **lattices**, not of solved packing problems. The packing problem is solved in
exactly five dimensions — 1, 2, 3, 8 and 24 — and **4 is not one of them**: D₄ is the densest
known packing in 4D and the proved densest *lattice*, but nobody has proved that no
non-lattice packing beats it. So "this 2D packing = this 3D packing = this 4D packing" is
true as a statement about the laminated lattices and false as a statement about optimal
packings, and that distinction is the whole content of this note.

The numbers below are tabulated in `rungs.py`, which recomputes the exact centre densities and
the published densities on `--selftest`. Every figure is either proved (marked) or the best
known packing on the source table; nothing here is a new claim.

---

## 1. Two questions that must not be run together

| question | best among | proved in |
|---|---|---|
| **densest lattice** | periodic lattices | n = 1, 2, 3, 4, 5, 6, 7, 8 and 24 |
| **densest packing** | *all* arrangements, lattice or not | n = 1, 2, 3, 8 and 24 |

The gap between the two rows is the trap. Dimension 4 has a proved densest lattice (D₄,
Korkine–Zolotareff 1872) and an unsolved packing problem. Dimensions 9–23 have neither.
Above dimension 3 the packing problem is solved in two dimensions only, 8 and 24, and both
proofs are from 2016–17 and rest on modular forms. That is not a gap in effort — it is the
shape of the subject.

**A second trap: density is not comparable across dimensions.** The density is the fraction
of space covered, and a ball fills less of its cell as the dimension rises, so the record
density falls from 0.907 in 2D to 0.740 in 3D to 0.0019 in 24D even though every one of those
packings is the best possible. The figure that does carry across dimensions is the **gain over
the cubic grid**,

    g_n = delta_n / delta(Z^n) = delta_n * 2^n ,

which is how much denser the record is than packing on the integer grid in the same
dimension. It is exact (and stored squared, so it is exact even when δ is a surd), and it is
the column to read if the question is "what does the dimension buy me".

---

## 2. The map, 1 to 24

`δ` is the centre density (spheres per unit volume at unit radius), `g` the gain over the grid.
`proved` means proved optimal among **all** packings; `lattice` means proved optimal only among
lattices; `—` means best known, nothing proved.

| n | record packing | δ | g | status |
|---:|---|---:|---:|---|
| 1 | Z | 1/2 | 1 | proved (trivial) |
| 2 | A₂ (hexagonal) | √3/6 | 2√3/3 ≈ 1.155 | proved (Thue 1910; Fejes Tóth 1940) |
| 3 | A₃ = D₃ (FCC) | √2/8 | √2 ≈ 1.414 | proved (Hales 2005) |
| 4 | D₄ | 1/8 | 2 | lattice only; packing **open** |
| 5 | D₅ | √2/16 | 2√2 ≈ 2.828 | lattice only |
| 6 | E₆ | √3/24 | 8√3/3 ≈ 4.619 | lattice only |
| 7 | E₇ | 1/16 | 8 | lattice only |
| 8 | **E₈** | 1/16 | **16** | proved (Viazovska 2017) |
| 9 | Λ₉ | √2/32 | 16√2 ≈ 22.63 | — |
| 10 | Best's 40-centre packing | 5/128 | 40 | — |
| 11 | Leech–Sloane 72-centre packing | 9/256 | 72 | — |
| 12 | K₁₂ (Coxeter–Todd) | 1/27 | 4096/27 ≈ 151.7 | — |
| 13 | Leech–Sloane 72-centre packing | 9/256 | 288 | — |
| 14 | Λ₁₄ | √3/48 | 1024√3/3 ≈ 591.2 | — |
| 15 | Λ₁₅ | √2/32 | 1024√2 ≈ 1448 | — |
| 16 | **Λ₁₆ = BW₁₆** (Barnes–Wall) | 1/16 | **4096** | — |
| 17 | Λ₁₇ | 1/16 | 8192 | — |
| 18 | 512-centre packing (Bierbrauer–Edel) | 19683/262144 | 19683 | — |
| 19 | record packing, 6 centres | ≈ 0.08896 | ≈ 4.66 × 10⁴ | — |
| 20 | record packing, 5 centres | ≈ 0.1559 | ≈ 1.64 × 10⁵ | — |
| 21 | record packing, 4 centres | ≈ 0.2100 | ≈ 4.40 × 10⁵ | — |
| 22 | record packing, 3 centres | ≈ 0.3326 | ≈ 1.39 × 10⁶ | — |
| 23 | record packing, 2 centres | ≈ 0.5005 | ≈ 4.20 × 10⁶ | — |
| 24 | **Λ₂₄** (Leech) | 1 | **2²⁴ = 16,777,216** | proved (Cohn–Kumar–Miller–Radchenko–Viazovska 2017) |

Two things this table says at a glance:

* the gain is not smooth. It grows by about ×1.9 per dimension from 9 to 13, by ×2 per
  dimension from 8 to 16, and by ×2.83 per dimension from 16 to 24: the record pulls away
  fastest in the dimensions nobody has solved;
* the centre density is **not monotone**. δ₁₂ = 1/27 > δ₁₃ = 9/256, and δ₁₁ = δ₁₃. "More
  dimensions pack better" is false in δ; what grows is the gain.

---

## 3. The chain that is real: lamination

The mechanism that connects the low dimensions is **lamination**, and it is exactly the
picture the question asks for. Start with the integer row. A row of touching circles is the
1-dimensional packing; a second row dropped into the hollows between the first row's circles
gives the hexagonal packing; a third layer in the tetrahedral hollows of the hexagonal layer
gives FCC; and the operation repeats:

    Λ₁ = Z  ⊂  Λ₂ = A₂  ⊂  Λ₃ = A₃ = D₃ = FCC  ⊂  Λ₄ = D₄  ⊂  Λ₅ = D₅
           ⊂  Λ₆ = E₆  ⊂  Λ₇ = E₇  ⊂  Λ₈ = E₈        (up to scale throughout)

Each rung is *two copies of the previous rung*, the second shifted by a deepest hole of the
first: **Λₙ₊₁ = Λₙ ∪ (Λₙ + u)** where `u` is a hole of largest covering radius. Stacking a
layer in the tightest place is the whole construction, and it is why these are called
laminated lattices (Conway–Sloane, *SPLAG* ch. 6).

Three exact identities are worth naming, because they are the ones the question's "=" is
entitled to:

| in 2D | in 3D | in 4D | why it is the same object |
|---|---|---|---|
| A₂, the hexagonal lattice | A₃ = D₃, FCC | D₄ | successive laminations: hexagon layers → FCC → D₄ |
| Voronoi cell: regular hexagon | Voronoi cell: rhombic dodecahedron | Voronoi cell: regular 24-cell | 6, 12, 24 facets = kissing numbers |
| δ = √3/6, g = 2/√3 | δ = √2/8, g = √2 | δ = 1/8, g = 2 | each is the densest *lattice* in its dimension |

For n ≤ 8 the laminated lattice is unique and is the proved densest lattice: Lagrange 1773
(n = 2), Gauss 1831 (n = 3), Korkine–Zolotareff 1872 and 1873 (n = 4, 5), Blichfeldt 1935
(n = 6, 7, 8). So on 2 → 3 → 4 → 5 → 6 → 7 → 8 the chain is not a metaphor; it is a theorem at
every step, for lattices. The packing problem on the same rungs is solved only at 2, 3 and 8.

**The 2D rung is a slice of the 3D rung, exactly.** The hexagonal lattice is the (111) plane
of FCC, and every FCC point is a hexagonal point plus one integer — the layer index. That map
is a bijection, reversible, and loses nothing; `bridge.py` builds it in integer arithmetic and
checks both round trips on an enumerated box. What it does *not* do is carry the density: the
3D gain comes from the stacking offset, which is not a symmetry of the 2D lattice. And which
slice you take is the whole question — the (001) slice of FCC is the *square* lattice, the one
the hexagonal packing beats by 2/√3. The full statement is in
[`BRIDGE.md`](BRIDGE.md).

**Does that reach squares-in-squares?** Not as an engine: that problem has a wall, a fixed
orientation and a density ceiling that is *attained* on 31 rows, so the bridge's objects are absent
and nothing in it can bound an `L`. In particular the `2/√3` between the (001) and (111) sections is
a ratio between two **sphere** relaxations — squares tile at density 1 in either section, so it is
not a cost the table pays and not a gap it could close. What does transfer is the section
vocabulary, and the reason the plane result reaches the table's *addressing* rather than its `L`.
The argument, with the table's own numbers, is in [`SQUARES.md`](SQUARES.md).

---

## 4. Where the chain breaks

The laminated ladder keeps going all the way to 24 — Λ₂₄ *is* the Leech lattice, the last
laminated lattice — but from 9 on it stops being the answer to either question:

| break | what happens |
|---|---|
| **n = 9** | Λ₉ is the densest known lattice, but optimality among lattices is open. It has been open since Blichfeldt: ∆(L)₉ is still unknown. |
| **n = 10, 11, 13** | a **periodic non-lattice** packing beats every known lattice — 40 centres per cell at 10 (Best 1980), 72 centres at 11 and 13 (Leech–Sloane 1971). |
| **n = 11, 12, 13** | even among lattices, Λ₁₁, Λ₁₂, Λ₁₃ are beaten by the Kappa lattices K₁₁, K₁₂ (Coxeter–Todd) and K₁₃. The densest known lattice at 12 is K₁₂, not Λ₁₂. |
| **n = 16** | the exceptional line resumes: Λ₁₆ = BW₁₆, the Barnes–Wall lattice, is the densest known lattice in 16 dimensions — but the linear-programming bound is provably more than 1.7× above it (Cohn–Tripathi), so the method that settled 8 and 24 cannot settle 16. |
| **n = 18–23** | all records are periodic non-lattice packings (2 to 512 centres per cell), several from the 2025 antipode construction. None is proved. |
| **n = 24** | Λ₂₄ = Leech, proved optimal among all packings and unique among periodic ones. Above 24 no dimension has a proved optimal packing. |

So the honest sentence is: **the 2D packing and the 3D packing are the same construction one
step apart; the 4D packing is the same construction with a proved-lattice-only status; and by
9 dimensions the construction is still running but it is no longer what is known to be best.**

---

## 5. The other ladder: codes to lattices

There is a second route up, and it is the one this repository actually lives on. Construction
A turns a binary code into a lattice, Construction B sharpens it, and the exceptional rungs
of the sphere-packing ladder are exactly the rungs this route reaches:

| dim | code | construction | lattice | kissing |
|---:|---|---|---|---:|
| 4 | even-weight code [4,3,2] | A | D₄ | 24 |
| 8 | extended Hamming [8,4,4] | A | E₈ = Λ₈ | 240 |
| 16 | Reed–Muller [16,5,8] | B | BW₁₆ = Λ₁₆ | 4,320 |
| 24 | Golay [24,12,8] | B / C | Leech = Λ₂₄ | 196,560 |

This is why 8, 16 and 24 are the exceptional dimensions and 4–7 are not: they are the
dimensions where a *doubly-even self-dual code* of the right length exists, and the
corresponding lattice is extremal. The 24-dimensional rung is the one the GLM uses — the A/B/C
ladder over the Golay code is `src/glm_universal/substrate/leech_construct.py`, and the
substrate study's theorem index (`source_material/done/substrate_study/glm_package/`) is
largely about what that rung can and cannot do.

The same two ladders are drawn in this repository already. `studies/CONSTRUCTION_LADDER_STUDY.md`
walks the 24-dimensional rungs as a *diamond* (Construction A and C are incomparable), and
`studies/HIGHER_LATTICE_STUDY.md` takes the rungs above Leech: BW₃₂ (Construction D over
RM(1,5) ⊂ RM(3,5), kissing 146,880) and the 48-dimensional ternary rung from the Pless
symmetry code. Those are density rungs above the
last proved dimension, not new optima — no dimension above 24 has a proved optimal packing.

---

## 6. What "this packing = that packing" may say

**Allowed:**

1. A₃ = D₃ = FCC — one lattice, three names; the 3D rung is the 2D rung laminated.
2. Λ₈ = E₈, Λ₁₆ = BW₁₆, Λ₂₄ = Leech — each is the laminated rung *and* the code rung.
3. δ₈ = δ₁₆ = δ₁₇ = 1/16 — three different dimensions, one centre density (this is checked
   exactly in `rungs.py`). The Leech lattice has 16 × the centre density of E₈.
4. The gains: 1, 2/√3, √2, 2, 2√2, 8/√3, 8, 16 for the first eight rungs, then 4096 at 16 and
   2²⁴ at 24.

**Not allowed:**

1. "The 4D problem is solved because 2D and 3D are." D₄ is proved only among lattices; the best
   upper bound on the 4D packing density is 0.6361, 3.2 % above D₄ (Cohn–de Laat–Salmon
   three-point bounds).
2. "Packing gets better as dimension rises." The centre density of the record falls from 12 to
   13 and is equal at 11 and 13; only the gain over the grid rises.
3. "The laminated rung is the record." From 9 on it is the record only sometimes, and at
   11, 12, 13 it is not the record even among lattices.
4. "8 and 24 are solved for a reason we understand." What is understood is the mechanism
   (below), not a general criterion.

---

## 7. Why 8 and 24, and not 4

The Cohn–Elkies linear-programming bound (2003) gives an upper bound on the density of any
packing from an auxiliary function `f` with `f ≤ 0` beyond the sphere diameter and `f̂ ≥ 0`.
The bound is sharp exactly when such an `f` can be found that matches a known packing. In 8
dimensions Viazovska built that `f` out of modular forms (quasimodular forms of level 1), and
in 24 dimensions Cohn, Kumar, Miller, Radchenko and Viazovska built its analogue. The two
lattices are also *universally optimal* (the same authors, 2019): among configurations of
equal density they minimise every completely monotone energy.

Dimensions 4–7 and 9–23 fail for two different reasons, and both are visible in the bound's
ratio to the best known density: 1.032 at 4, about 1.09–1.10 at 5–7, 1.31 at 9, 1.70 at 16.
At 8 and 24 the ratio is 1. Hundreds of millions of times more is unknown in 24 dimensions
than in 8, and yet 24 is solved and 4 is not; the reason is that dimension 24 is where the
Leech lattice's theta series is a modular form of weight 12 (`E₄³ − 720Δ`, which the
substrate's `leech2.theta_series` computes), and 8 is where E₈'s is a form of weight 4. There
is no such object at 4, 5, 6, 7 or 12, and at 12 and 16 Cohn and Tripathi proved that the LP
bound is at least 1.686× and 1.7× too weak to settle them. Dimension 4 is not unsolved
because the technique is missing — the technique does not apply, and no one knows what would.

Peter Sarnak's summary of Viazovska's paper — "stunningly simple, as all great things are" —
is about the proof, not about why the answer exists in 8 and 24 and nowhere else. That
"why" is genuinely not understood, and it is the honest reason the ladder has holes.

---

## 8. What is open

| dimension | state | how far the record could be from optimal |
|---:|---|---|
| 4 | D₄ best known; packing open | upper bound 3.2 % above |
| 5, 6, 7 | D₅, E₆, E₇ best known; lattices proved | about 9–10 % above |
| 9–23 | best known only; lattice optimality open from 9 | 31 % at 9, 70 % at 16, 88 % at 13 |
| 24 | solved | — |
| > 24 | nothing proved; records only | grows fast |

The four-dimensional case is the sharpest open question on this ladder, and it is a
well-posed one: prove that no packing of unit balls in R⁴ has density above π²/16.

---

## 9. What this note does not claim

* No new mathematics. Every row is quoted from the source table, and the only computed
  quantities are identities that follow from the definition of centre density.
* Rows marked `—` are **best known**, not optimal. The records at 18–23 are recent and can
  move again.
* For n ≥ 10 the cell determinant stored in `rungs.py` is the value implied by the published
  density, so the exact check there is a consistency check on the stored triple, not
  independent evidence. For n ≤ 8 and n = 24 the determinant and minimal norm are the
  lattice's own published invariants, so the check is real.
* The published-density check uses floats. It is a transcription check on 24 decimal strings,
  not a proof, and it is labelled as such in the code.
* `bridge.py` verifies the A₂-in-D₃ slice and the `D₂ … D₅` layer bijections exactly. The
  `Λ₂₄ ≅ A₂ × Z²²` composition is quoted from the laminated construction, not verified.

---

## 10. Sources

Read for this note; the densities in §2 are Cohn's table.

* H. Cohn, *Sphere packing* (table of best known densities, dimensions 1–48, with upper
  bounds), <https://cohn.mit.edu/sphere-packing/>.
* M. S. Viazovska, *The sphere packing problem in dimension 8*, Ann. of Math. **185** (2017),
  991–1015. ∆₈ = π⁴/384.
* H. Cohn, A. Kumar, S. D. Miller, D. Radchenko, M. Viazovska, *The sphere packing problem in
  dimension 24*, Ann. of Math. **185** (2017), 1017–1033. ∆₂₄ = π¹²/12!.
* H. Cohn, A. Kumar, *Optimality and uniqueness of the Leech lattice among lattices*, Ann. of
  Math. **170** (2009), 1003–1050.
* T. Hales, *A proof of the Kepler conjecture*, Ann. of Math. **162** (2005), 1065–1185;
  Flyspeck formal verification, 2017.
* A. Thue (1910) and L. Fejes Tóth (1940) for the plane; Gauss (1831) for the 3D lattice;
  Korkine–Zolotareff (1872, 1873) for the 4D and 5D lattices; Blichfeldt (1935) for 6–8.
* J. H. Conway, N. J. A. Sloane, *Sphere Packings, Lattices and Groups*, 3rd ed., Springer
  1999 — ch. 1–6, and ch. 6 for laminated lattices.
* N. J. A. Sloane, *The sphere packing problem*, ICM 1998, Doc. Math. Extra Vol. III, 387–396.
* H. Cohn, D. de Laat, A. Salmon, *Three-point bounds for sphere packing*, arXiv:2206.15373 —
  the dimension-4 upper bound.
* H. Cohn, A. Tripathi, *Dual linear programming bounds for sphere packing via modular forms*,
  arXiv:1909.04772 — the 12- and 16-dimensional LP bounds.
* R. Chen, J. Hu, B. Li, L. Wang, T. Wu, *New sphere packings from the antipode construction*,
  arXiv:2505.02394 — several records at 18–23.
* Error Correction Zoo, *Λ₁₆ Barnes–Wall lattice*, <https://errorcorrectionzoo.org/c/lambda16>.
* In this repository (paths from the repository root, written as code because this item is
  moved between `ToDo/` and `done/`): `studies/CONSTRUCTION_LADDER_STUDY.md`,
  `studies/LEECH_SHELLS_STUDY.md`, `studies/HIGHER_LATTICE_STUDY.md`,
  `src/glm_universal/substrate/README.md`,
  `source_material/done/substrate_study/glm_package/README.md`.

## 11. Re-running

```bash
cd source_material/ToDo/dimension_ladder   # or done/, if the item has been filed
python3 rungs.py              # the table, with exact centre densities and gains
python3 rungs.py --selftest   # 18 determinant identities, 24 gains, 24 published densities
python3 bridge.py             # the 2D layer of the 3D lattice, exact, both ways
```
