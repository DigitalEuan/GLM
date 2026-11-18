# The bridge: the 2D optimal packing as a layer of the next lattice up

## The question

If the 2D optimal packing has an equivalent in lattice terms, is there a bridge
to the first lattice up that is reversible and loses nothing? And if so, what
does it say?

## The answer

**Yes, and it is exact: the densest plane lattice is literally a slice of the
densest 3D lattice, and the slice-to-point map is a bijection with one integer.**
Every point of the face-centred cubic lattice is a point of the hexagonal layer
plus an integer saying which layer; every hexagonal layer point plus an integer
is an FCC point; nothing is lost in either direction. `bridge.py` builds the map
in integer arithmetic and checks both round trips on a box.

What it will not do is carry the density. The 3D gain over the grid is *not* the
2D gain times something; the difference is created by the **stacking offset**,
which is not a symmetry of the 2D lattice. That is the whole finding, and it is
sharp enough to be worth stating in three pieces.

## The construction (all integer arithmetic)

* **the layer** `L = {v ∈ Z³ : v₁+v₂+v₃ = 0}`. Its shortest nonzero vectors are
  the six permutations of `(1,−1,0)`, so its minimal squared norm is 2; a basis is
  `(1,−1,0), (0,1,−1)` with Gram determinant 3. This is A₂ scaled by √2 — the
  densest plane lattice, centre density `δ² = (2/4)²/3 = 1/12`.
* **the lattice** `D₃ = {v ∈ Z³ : v₁+v₂+v₃ even}` — FCC: minimal squared norm 2,
  Gram determinant 4, `δ² = (2/4)³/4 = 1/32`.
* **the bridge** for `v ∈ D₃`, put `s = v₁+v₂+v₃` (even) and `m = s/2`:

      φ(v)        = ( v − m·(1,1,0),  m )        ∈ L × Z
      φ⁻¹(p, m)   = p + m·(1,1,0)

  `φ(v)` has coordinate sum 0, so it is in `L`; `p + m·(1,1,0)` has sum `2m`, so
  it is in `D₃`. Hence `D₃ ≅ L × Z` exactly. The layer at height `2m` is
  `L + m·(1,1,0)`; reduced mod `L` the offset takes three values, which is the ABC
  stacking of close-packed layers.
* **the same step repeats** along a coordinate axis:
  `D_{n+1} → D_n × Z`, `v ↦ (v' − (v_{n+1} mod 2)·e₁, v_{n+1})`, with inverse
  `(p,k) ↦ p + (k mod 2)·e₁ + k·e_{n+1}`. So `D_n ≅ L × Z^{n−2}` by composition.

## What the checks say

`python3 bridge.py` (exact, no square root ever formed):

| object | minimal shell | Gram det | centre density² |
|---|---|---:|---:|
| `L` = A₂ layer, the (111) plane | 2, six vectors | 3 | **1/12** |
| `D₂`, the (001) plane | 2, four vectors | 4 | **1/16** |
| `D₃` = FCC | 2, twelve vectors | 4 | 1/32 |
| `D₄` | 2, twenty-four vectors | 4 | 1/64 |
| `D₅` | 2, forty vectors | 4 | 1/128 |

and the bijections `D₃ ↔ L × Z`, `D₄ ↔ D₃ × Z`, `D₅ ↔ D₄ × Z` hold both ways on
every point of an enumerated box (171, 1,201 and 8,403 points respectively).

## The three things it says

1. **The 2D optimum is a layer of FCC — but which layer is the whole question.**
   Slicing `D₃` by `z = 0` gives `D₂`, the *square* lattice, with `δ² = 1/16`.
   Slicing it by `v₁+v₂+v₃ = const` gives A₂, with `δ² = 1/12`. The ratio is
   exactly `4/3` in the square, i.e. `2/√3` in δ — **which is precisely the 2D
   gain of the hexagonal packing over the square one**. The same 3D lattice
   carries both the optimal 2D packing and the packing it beats; the bridge only
   names the optimum if you take the right plane.
2. **The bridge is lossless and reversible.** One integer per extra dimension, no
   residue, no rounding. Every Leech-scale question about "is this point there"
   reduces to a layer point and a few integers.
3. **The bridge does not preserve density, and the reason is exact.** The layer
   spacing is `2/√3` (the distance between planes of constant coordinate sum), and

       (area of L)² × (spacing)² = 3 × 4/3 = 4 = det Gram(D₃),

   so the 3D cell is exactly one layer's worth of area times the stacking
   spacing — additive accounting, not a multiplication of densities. The gain
   rises from `2/√3 ≈ 1.155` to `√2 ≈ 1.414` because of the offset `m·(1,1,0)`,
   and that offset is not in `L` (its coordinate sum is 2, not 0). In one
   sentence: **the layer is the packing, and the gain is the stacking.**

## What it refuses to say

* It does not say the 2D packing *determines* the 3D one. `φ` is a bijection, not
  an isometry: distances in `D₃` are not functions of distances in `L` and `m`
  alone, and the offset is the extra information.
* It does not say anything about the *packing problem's* optimality in 4D or in
  9–23. The bijection holds for the lattice, not for the optimum (see the note's
  §1 and §4).
* It does not upgrade the 2D result: A₂ optimality is 2D optimality, and the
  bridge is a change of coordinates, not a proof transfer.
* It says nothing usable *as machinery* about squares-in-squares, which has a wall,
  a fixed orientation and no bulk density to maximise — see [`SQUARES.md`](SQUARES.md)
  for what it does say about that table (a diagnosis, not a bound).

## To 24 dimensions

The same decomposition holds rung by rung for the laminated lattices — each
`Λ_{n+1}` is two layers of `Λ_n` (Conway–Sloane, *SPLAG* ch. 6) — so

    Λ₂₄ ≅ A₂ × Z²²

as a set: two continuous coordinates of the 2D optimum plus 22 integers address
every Leech point, reversibly and losslessly. That composition is **quoted, not
verified here**: `bridge.py` verifies the A₂-in-D₃ slice and the `D₂ … D₅`
bijections, because those are the ones it can enumerate exactly. A machine check
of the full 24-rung composition would need the explicit laminated shifts for each
rung, which is a different and larger instrument.

## Re-running

```bash
cd source_material/ToDo/dimension_ladder
python3 bridge.py     # the verdicts, asserting as it prints
```
