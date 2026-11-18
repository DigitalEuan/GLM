# 16 — The missing object: a map from a 2D packing to Λ₂₄

**Run 45, 2026-11-18.** Instrument `scripts/leech_map.py`; ledger
`workspace/push/leech_map.json`. Read-only.

`15-LEECH-24D-DESIGN.md` ended on the honest statement that the Leech lattice is
not the problem — the map from a square packing to a point of Λ₂₄ is. This run
builds the map, proves where it can exist at all, validates the lattice test
exactly, and measures what it sees. The result is a sharp structural answer:
**the map exists, it is exact, and it is provably blind to the only geometry that
scores.**

---

## 1. Where the map can exist (the window)

A packing of n unit squares in a side-L square is: n centres (2n numbers), n
angles (discrete: 0 or π/4), and L. Translation is a genuine symmetry of the
packing — sliding it does not change the packing — so it is modded out by putting
the bounding box at the origin. What remains is

```
continuous dimension = 2n + 1.
```

A Λ₂₄ point is 24 numbers. Therefore a lossless, reversible map exists exactly
for

```
2n + 1 ≤ 24   ⟺   n ≤ 11,
```

with one coordinate to spare at n = 11. **For n ≥ 12 no injective continuous map
exists at all** — every "address" there is a lossy feature map, which is what
`leech_address.py` built (6 angle sectors × 4 shells) and measured to carry no
score after conditioning on rotation.

So the holy grail is real but *bounded*: it lives on n ≤ 11, and the delivered
table's mass (989 of 1000 rows, n ≥ 12) is outside it by dimension alone. That is
not a failure of nerve; it is a counting argument, and it is the first thing to
know before designing anything.

**A failed first attempt, recorded.** The first version of the map used the *gap*
vector (n+1 gaps per axis, 2n+2 numbers) on the theory that a 1D packing *is* its
gaps. The round trip destroyed that in one run: at n = 10 and n = 11 the
reconstruction error was ~1.9 — because in 2D a packing **stacks** squares (a
column shares its x-range), so along an axis the projections overlap, the "gaps"
go negative, and the identity `Σg = L − Σe` is false. Gaps are a coordinate
system only for a single row. Positions are the honest basis, and their count is
2n+1, not 2n+2.

## 2. The map, exactly

```
skeleton(state)  -> angles                       discrete, n bits
encode(state,S)  -> 24 ints = round(S·[x₁..xₙ, y₁..yₙ, L])   zero-padded
decode(ints,angles) -> state                     reversible up to 1/(2S)
```

`S` is a declared integer scale; the only loss is the rounding, and the only
gauge is the translation, which is a symmetry rather than a loss. Measured round
trip on the eleven delivered rows in the window (S = 256):

| n | L | 1/(2S) bound | measured error |
| ---: | ---: | ---: | ---: |
| 1..9 | 1.0 – 3.0 | 0.00195 | ≤ 1.3e-9 |
| 5 | 2.707106782 | 0.00195 | 1.92e-03 |
| 10 | 3.707106783 | 0.00195 | 7.6e-05 |
| 11 | 3.877083592 | 0.00195 | 1.82e-03 |

The rows that are exactly representable come back exactly; the √2 rows come back
within the rounding bound. The codec works.

## 3. The lattice test, validated (not assumed)

`in_leech24` implements the exact integer form the repository's
`LeechResidue.lean` states: *all coordinates share a parity m; Σx ≡ 4m (mod 8);
each nonempty residue class mod 4 is a Golay codeword.* A test is only worth what
its validation is worth, so it was checked against the complete set of minimal
vectors of √8·Λ₂₄ (squared norm 32):

| family | count | accepted |
| --- | ---: | ---: |
| (2⁸, 0¹⁶) on the 759 octads, even number of minus signs | 97 152 | 97 152 |
| (∓3, ±1²³), one coordinate of magnitude 3 | 98 304 | 98 304 |
| (±4², 0²²) | 1 104 | 1 104 |
| **total** | **196 560** | **196 560** |

and it rejects the short impostors that a loose test would accept: 2eᵢ, 4eᵢ,
2⁴, 2², 1⁸ — none accepted. The first version of family B was wrong (it flipped a
sign without preserving the residue classes) and the validator said so: 0 of
98 304 accepted. That is the instrument doing its job twice in one run.

**Consequence for the repository:** "is this a Λ₂₄ point" is now a decidable
predicate, not a slogan. That is a GLM module in its own right.

## 4. What it sees — and the one result that matters

Delivered rows, legality of the encoded vector at any scale in
{1, 2, 4, 8, 16, 64, 256, 1024}:

| n | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
| --- | - | - | - | - | - | - | - | - | - | - | - |
| legal at | 8–1024 | 8–1024 | 8–1024 | 8–1024 | **none** | 8–1024 | 8–1024 | 8–1024 | 8–1024 | **none** | **none** |
| L | 1 | 2 | 2 | 2 | 2.7071 | 3 | 3 | 3 | 3 | 3.7071 | 3.8771 |

Every legal row is a grid or a near-grid; the three rows that are **not** legal
are exactly the three whose side contains a 45° square (n = 5, 10, 11 — the only
rows in the window with L ∈ ℤ + ℤ√2/2).

The jitter ensembles (40 outward perturbations per n, all feasible, scores
spanning the stated ranges) turn that into a crosstab with no off-diagonal:

|  | legal at some scale | legal at none |
| --- | ---: | ---: |
| **contains a 45° square** | **0** | 87 |
| **no tilted square** | 168 | **0** |

**255 rows, perfect separation.** The lattice condition is an
integrality/rationality condition: a 45° square injects √2/2 into the coordinates
and into L, so at every integer scale the encoded vector sits off the rational
lattice that the Golay/parity conditions describe. And the tilted rows are
*precisely* the rows that beat the grid — the whole reason the r = 1 column
exists (`pl32_base.py`, slack 0.52–0.71, all of it from √2 geometry).

This is a **structural** obstruction, not the statistical one measured before.
`leech_address.py` found MI ≈ 0 *after conditioning*; this says something
stronger and simpler: the address cannot represent the tilted configurations at
all, and the tilted configurations are the score.

## 5. What this means for the design

1. **The address route is closed for score purposes** — and now for a reason.
   Not "the lattice does not correlate with the score", but "the lattice's
   legality predicate is incompatible with the algebraic field the score lives
   in". No choice of scale fixes it: the separation holds across eight scales
   spanning three orders of magnitude.
2. **The map is not useless — it is a codec.** A 24-integer canonical form for
   any packing with n ≤ 11, exact to 1/(2S), with a validated membership
   predicate and a computable Golay coset. That is a legitimate GLM module
   (`leech_map.encode/decode/in_leech24/snap_distance`), useful for storage,
   comparison and deduplication of small-n packings — which is what the control
   cases (n = 5, n = 11) are.
3. **The right discrete address is combinatorial, not metric.** The measurement
   says the design can see exactly one bit per square — *tilted or not* — and
   nothing else. So the address this project should build is
   `(tilt pattern, contact graph)`: exact, scale-free, invariant under the
   container's D₄ symmetry, and *complete* for the combinatorial part of a
   packing. It would be a genuine invariant (two packings with the same address
   are combinatorially the same), unlike every metric quantisation tried so far.
   That is the next object, and it is testable with this same instrument: does
   the address predict the row's slack, after conditioning on n and r?
4. **The move-source route stays open.** The 23 deep-hole types remain the only
   24D structure that can produce *moves* rather than addresses
   (`15-LEECH-24D-DESIGN.md` §8, T2).

## 6. Honest limits

* The window excludes 989 of 1000 delivered rows by dimension. Nothing here says
  anything about n ≥ 12 except that no injective map exists there.
* The ensembles are outward jitters of the delivered rows: feasible, but narrow
  in score (ranges are ≤ 0.011 wide). The tilt/legal separation is measured on
  255 rows at 8 scales; the conjecture "tilted ⟹ never legal at any integer
  scale" is supported by that and by the field argument, not proved.
* Legality of the *rounded* vector is not automatic from irrationality — rounding
  always produces integers, so the 0/87 is a measurement, and the field argument
  explains why it should hold, not that it must.
* No score is claimed, no row changed, nothing committed.

## 7. Files

* `scripts/leech_map.py` — `skeleton`, `encode`, `decode`, `in_leech24`,
  `snap_distance`, `minimal_vectors`, `validate`, `probe`. `--validate`,
  `--probe`, or both. 3.2 s, all checks pass.
* `workspace/push/leech_map.json` — ledger: validation counts, per-row legality,
  ensembles, and the tilt × legality crosstab.
* Related: `15-LEECH-24D-DESIGN.md` (the design and the projection/section
  algebra), `10-LEECH-ADDRESS.md` (the pocket address and its MI), 
  `src/lean/.../LeechResidue.lean` (the integer form used here).
