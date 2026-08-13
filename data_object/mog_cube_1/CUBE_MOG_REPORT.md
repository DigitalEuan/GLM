# The cube surface as the MOG: what is proved, what failed, what it costs

This report covers the work in

| file | contents |
|---|---|
| `RequestProject/CubeSurfaceMOG.lean` | the identification *cube surface = MOG grid*, the three-layer factorisation, face erasure, hexacode decoding |
| `RequestProject/CubeStabiliser.lean` | Experiment 1 — which of the 48 cube symmetries are free |
| `RequestProject/CubeTax.lean` | the price list: syndrome, coset leaders, covering radius, `TAX ≤ 4Q` and its sharpness |
| `RequestProject/MeasuredWords.lean` | words with tangible, measurable content (physical dimension) on the cube |
| `RequestProject/MeasuredSentences.lean` | generating sentences that make sense, and measuring how often the cube agrees |
| `glm_clean/exp7_cube_surface.py` | the exhaustive searches that guided the above (Python, not machine-checked) |

Everything stated as "proved" below is a Lean theorem that compiles with no
`sorry` and no extra axioms. Everything found only by the Python search is
labelled as such.

---

## 1. The coordinate map

A surface cell of the cube is a *(corner, axis)* pair: 8 corners × 3 faces at
each = 24. Equivalently, a cell is a **face** (an axis plus a sign — six of
them) together with a **quadrant of that face** (the signs of the other two
axes — four of them):

```
24 surface cells  =  6 faces × 4 quadrants  =  6 columns × 4 rows of the MOG
```

Row `i` of a face carries the GF(4) label `rowLabel i ∈ {0, 1, ω, ω̄}`, the
**face symbol** is the GF(4) sum of the labels of that face's set cells, and a
grid is a codeword (`CubeMOG.IsMog`) when

1. the six face symbols form a hexacode word, and
2. every face has the parity of the top row.

This is the dimension-exact identification the brief asked for, and it is a
*choice of coordinates* — §3 below shows that a different choice buys more
symmetry.

## 2. The three-layer factorisation — proved

```
2^24 patterns  --face symbols-->  2^18  --parity rules-->  2^12
```

* `CubeMOG.fibre_card` — each face's 16 patterns map onto its 4 GF(4) symbols
  with fibres of size exactly 4 (layer 1: cells interact *within* a face).
* `CubeMOG.hexpass_card = 2^18` — `64 × 4^6` patterns survive the hexacode
  (layer 2: faces interact *only* through their single GF(4) symbol).
* `CubeMOG.mog_card = 2^12` and `CubeMOG.parity_layer_factor` — the parity
  rules supply the remaining factor `2^6` (layer 3: the global wrap-around).
* `CubeMOG.mog_weight_enumerator` — the resulting code has the Golay weight
  distribution `1, 759, 2576, 759, 1`, and `CubeMOG.mog_min_weight` gives
  `d = 8`.

So the interaction sparsity in the brief is exact: cross-face interaction is
compressed to one GF(4) symbol per face, and nothing else crosses.

## 3. Experiment 1 — the stabiliser test

**Result (proved): 12 of the 48 cube surface symmetries are free.**

`CubeStab.stabiliser_card = 12`, and `CubeStab.preserves_iff_tetrahedral`
identifies them exactly: the symmetries with an even axis permutation *and* an
even number of sign flips — the rotation group of an inscribed **tetrahedron**,
`T ≅ A₄`. All 12 are rotations; `CubeStab.quarterTurn_not_preserving` is a
named witness that a quarter-turn of a face is a rotation that is *not* free.

**But that is a fact about the placement, not about the cube.** A different
placement of a Golay code on the same 24 cells does better:

* `CubeStab.oCode_rotations_free` — the code spanned by `oBasis` (a genuine
  `[24, 12, 8]` code: `oCode_card`, `oCode_min_weight`,
  `oCode_weight_enumerator`) is preserved by **all 24 rotations**;
* `CubeStab.oCode_improper_priced` — and by **no** improper symmetry.

**Not machine-verified:** an exhaustive search over `G`-invariant subspaces
(`glm_clean/exp7_cube_surface.py`, `invariant_golay_codes`) reports that 24 is
the ceiling — no Golay code on the cube's surface is invariant under the full
order-48 group `O_h`, nor under `T_d`; `T_h` and the rotation group `O` both
admit invariant Golay codes. Only the positive half of that (an explicit
`O`-invariant code exists) is proved in Lean.

So the honest answer to "is the cube's geometry native to the code?" is:
*half of it is, and which half depends on the coordinate map.* With the
canonical MOG placement you get the tetrahedral 12; with `oBasis` you get all
24 rotations free and all 24 reflections priced.

## 4. Experiment 2 — one bad face heals, two do not

* `CubeMOG.face_erasure_correctable` — two codewords agreeing outside one face
  are equal: a single erased face is always reconstructed.
* `CubeMOG.two_face_ambiguous` — for **every** pair of faces there is a nonzero
  codeword supported on those two faces (two full faces form an octad). So a
  two-face erasure is genuinely ambiguous, for every pair. This is sharper than
  the prediction in the brief: it is not "at the boundary", it *always* fails.
* One layer up, the same boundary: `GolayHex`/`CubeMOG.hexacode_min_dist` gives
  `d = 4` for the `[6,3,4]` hexacode, `hexacode_unique_decode` gives unique
  correction of one symbol error, and `hexacode_ambiguous_at_two` exhibits an
  explicit distance-2 word that two codewords are equidistant from.

## 5. The price list — proved, and sharp

`CubeTax.synd` is the 12-bit syndrome: three GF(4) hexacode residuals (faces
3, 4, 5 against the re-encoding of faces 0, 1, 2) plus six parity residuals. It
vanishes exactly on codewords (`synd_eq_zero_iff`) and is linear
(`synd_gxor`) — so the syndrome of a damaged grid depends only on the damage.

| operation class | status | proved |
|---|---|---|
| XOR with a codeword | free | `CubeTax.xor_codeword_free` |
| rotations (right placement) | free | `CubeStab.oCode_rotations_free` |
| reflections | priced | `CubeStab.oCode_improper_priced` |
| AND / OR of faces | priced | `CubeTax.and_is_priced` |
| repair of any damage | `≤ 4·Q` | `CubeTax.tax_le_four_Q` |
| repair below the boundary | unique | `CubeTax.repair_unique_of_le_three` |
| repair at distance 4 | ambiguous — must read | `CubeTax.repair_ambiguous_at_four` |

The `≤ 4Q` claim of the brief is now a theorem in both directions:

* `CubeTax.covering_radius_le_four` — every one of the `2^24` grids is within 4
  cells of a codeword (proved by building a coset-leader table from all 12951
  grids of weight `≤ 4` and checking it against all 4096 syndromes inside
  Lean);
* `CubeTax.covering_radius_ge_four` — a full face (weight 4) is at distance
  exactly 4 from the code, so `4Q` is the true worst case, not an over-estimate.

## 6. Words with measurable content

The brief's own steer: *use words whose information is tangible and
measurable*. The most tangible content a physics word has is its **dimension** —
the integer exponents of `L, M, T, I, Θ, N`.

`MeasuredWords.dimWord` puts that on the cube: dimension `d` is carried by the
top cell of face `d`, and the rest of the grid is filled in by the code, so

* every measurable word is a lawful codeword — holding it costs nothing;
* multiplying quantities is exactly XOR of their codewords
  (`dimWord_mul`) — composition is the *free* operation;
* losing a face is losing one dimension's channel, and it is repaired
  (`dimension_channel_repairable`).

`MeasuredWords.accepts_true_equations` — the cube accepts `E = mc²`, `F = ma`,
`E·t = ħ`, `p = mv`, `P = E/t`, `Q = It`, and rejects `E = mc`.

### The ceiling, stated honestly

`MeasuredWords.dimWord_eq_iff` — the cube's verdict is *exactly* "the exponents
agree **mod 2**". So:

* `mod_two_blindness_witness` — **`E = mc⁴` is accepted although it is false.**
* `xor_encoding_is_mod_two` — and this is not a defect of this placement:
  **any** encoding whose composition is XOR is blind to exponent differences
  of 2. No better linear code fixes it; only a nonlinear (priced) operation, or
  keeping the integer exponent alongside the codeword, can.

The price structure around the verdict is all-or-nothing: an accepted equation
costs `0` (`accepted_tax_zero`), a rejected one costs at least `8·Q`
(`taxOf_detected`) because the difference of two codewords is a codeword of
weight `≥ 8`. There is no cheap dimensional error.

## 7. Generating sentences that make sense — with the failure rate measured

`MeasuredSentences` runs the end-to-end experiment on a vocabulary of 12
measurable words plus all 144 two-word products = **156 phrases**
(`phrases_count`), and all ordered pairs of differently named phrases as
candidate sentences.

| quantity | value | theorem |
|---|---|---|
| sentences that make sense (dimensions genuinely equal) | **356** | `equations_count` |
| sentences the cube accepts | **1758** | `substrate_count` |
| of those, dimensionally **false** | **1402** | `substrate_false_positive_count` |

* `equations_are_accepted` — the generator is **sound for the substrate**:
  every sentence that makes sense is accepted, and by `equations_tax_zero` it
  costs nothing. No true sentence is ever rejected.
* `substrate_false_positive_count` — and the cube's own filter is **not
  complete**: precision `356/1758 ≈ 20%`. `length_vs_acceleration` is a
  concrete case: the cube cannot tell a length from an acceleration.

That 20% *is* the measured cost of the characteristic-2 ceiling, and it is the
main negative result here. The usable conclusion:

> The Golay/MOG layer is an excellent **carrier** for measurable meaning — free
> composition, free storage, one-face repair, a sharp `4Q` worst-case repair
> price — but it is not by itself a **semantic decision procedure**. Used
> alone as an acceptance test it admits four false sentences for every true
> one. Semantics has to keep the integer content; the cube's contribution is
> to move and protect it for free.

## 8. What was not achieved

* No Golay placement invariant under the full 48-element cube group was found;
  the Python search says none exists, and that search is **not** verified in
  Lean.
  *(Later note, added when the package was finished: this is now a theorem, not
  a search — `GolayInv.no_Oh_invariant_golay` and `no_Td_invariant_golay` in
  `RequestProject/GolayInvolution.lean`. See `FINAL_REPORT.md` §6.)*
* The mod-2 ceiling was not overcome. A nonlinear, priced dimension check would
  be needed, and none is formalised here.
* The brief's "two bad faces → at the decoding boundary / ambiguous" is, on the
  cube-surface placement, strictly worse than a boundary: *every* two-face
  erasure is ambiguous (`two_face_ambiguous`).
* The 9-neighbour pressure of TGIC remains a stipulation; nothing here
  calibrates it against the correction radius 3 or the covering radius 4,
  beyond the fact that both of those numbers are now theorems
  (`repair_unique_of_le_three`, `covering_radius_le_four`,
  `covering_radius_ge_four`).
