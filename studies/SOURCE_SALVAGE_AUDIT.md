# The archive retrievals, recomputed

*[`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md) is the Lean half of the
archive round: what the supplied archive claimed, and what of it is a theorem.
This document is the **runtime half**. Every number those Lean files prove is
recomputed here from the substrate the package already carries, so the audit is
a measurement rather than a quotation, and a claim that stopped being true would
fail the suite rather than age quietly in a paragraph.*

Module: [`overlay/glm_universal/reasoning/salvage.py`](../overlay/glm_universal/reasoning/salvage.py)
— one call, `salvage_report()`, returns every section below.
Tests: `overlay/glm_universal/tests/test_salvage.py` — 24 test methods.
Specification: the eleven Lean files named in the table, by directive D8.
Arithmetic: exact `int` and `Fraction` throughout (D7). The two archive scores
that are irrational are returned as a **bracket**, never as a rounded decimal.

Recompute everything in this document with:

```bash
cd overlay
PYTHONPATH=. python3 -c "from glm_universal.reasoning.salvage import salvage_report as r; print(r())"
```

---

## 1. What is being audited, and why twice

The archive's claims were retrieved as Lean because Lean is where a claim stops
being an assertion. But a Lean theorem about *a* Golay code says nothing about
*this* package's Golay code unless the two are the same object, and a proof
about an abstract polygon count says nothing about the number the runtime would
produce. So each retrieval is checked a second way here: the same quantity is
recomputed from `glm_universal.substrate`, and the two are required to agree.

Three of the eleven turn up a discrepancy with the archive's own numbers, and
those are the interesting ones — a sampled mean that is exactly 6, a length that
is chosen rather than forced, and a "theorem" whose content is Euler's totient.
They are recorded in §4.

| Lean file | archive source | what it settles |
|---|---|---|
| `Lightspeed.lean` | `light/aristotle_01`, `light/EM_calibration_1` | the calibration chain is circular in `c`; the refractive-index law is what survives, and its `16/9` ceiling is already exceeded by diamond |
| `GolayWeightEnum.lean` | `data_object/mog_cube_1` | the weight enumerator of the substrate's own code, and the octad as the tax-minimising weight |
| `Packing.lean` | `data_object/FirstPrinciples` | a perfect three-error-correcting binary code has length 7 or 23; 24 is the parity extension |
| `Totient.lean` | `GMHGL/spatial_totient_kinetics.py` | the sub-cycle count of an `N`-gon is `⌊N/2⌋ − φ(N)/2`, and it vanishes exactly at the primes |
| `Steiner.lean` | `data_object/mog_cube_1/…/GolaySteiner.lean` | `S(5, 8, 24)`: every five-set lies in exactly one octad |
| `DimensionCarrier.lean` | `glm_lean/RequestProject/GLM.lean` | an `F₂` carrier cannot be primary, and the base-9 box `[−4,4]⁷` is the largest a 24-bit word holds |
| `Extraspecial.lean` | `glm_lean/RequestProject/GLM3.lean` | the plus-type count of `Λ/2Λ`, and the involutions of `2^(1+24)` above it |
| `Platonic.lean` | `GMHGL/value_geometry.py` | the "144 degree Platonic structure" is Euler's formula |
| `LDP.lean` | `GMHGL/ldp_complete_mapping.md` | Literal Data Physics: energy, descent, mass defect, rigidity, forbidden zone |
| `Triad.lean`, `TriadCensus.lean` | `GMHGL/tgic_*.py` | the 3-6-9 counts are generic; 44 of the 759 octads score a perfect 1 |

---

## 2. The retrievals, measured

### 2.1 Lightspeed — the chain returns what it was given

The archive's calibration runs molar Planck constant → work energy → tick →
cell duration → cell length, and reads a speed off the last two. Recomputed
exactly:

| quantity | exact value |
|---|---|
| molar Planck constant | `19951563564467157 / 5·10²⁵` |
| work energy | `19 / 60221407600000000000` |
| tick | `19951563564467157 / 9.5·10³⁰` |
| cell duration | `538692216240613239 / 9.5·10³⁰` |
| cell length | `80747931806120481173575731 / 4.75·10³⁰` |

**`c` comes back for every anchor.** The sweep covers 20 anchors and every tick
budget, and recovers `c` in all 20: `c_recovered_every_time` is `True`. It has
to, because `c` is used once, to turn the cell duration into a cell length, and
the division undoes the multiplication. An action and an energy generate no
speed.

**What survives is dimensionless.** The propagation law `n(T) = (24+T)/(24+T₀)`
is exact rational at every tax:

| tax `T` | 0 | 3 | 8 | 16 | 24 |
|---|---|---|---|---|---|
| `n(T)` | `8/9` | `1` | `32/27` | `40/27` | `16/9` |

The reference tax is the minimum admissible one (the octads, at `8Q`), and the
law's ceiling at `T = 24` is `16/9 ≈ 1.78`. Diamond's refractive index is
`2417/1000`, so the ceiling is already exceeded by a material anyone can buy:
the law is falsified as a law of optics, and kept as a statement about the
substrate's tax.

### 2.2 The code's own weight enumerator

All 4,096 codewords enumerated, not sampled: `1 + 759x⁸ + 2576x¹² + 759x¹⁶ +
x²⁴`. Minimum non-zero weight 8, every weight divisible by 4 (`doubly_even`),
and the enumerator the runtime computes agrees with the one `GolayWeightEnum.lean`
proves.

### 2.3 Packing — 23 is forced, 24 is chosen

`perfect_lengths` searches to length 2,000 and returns exactly `(7, 23)`. At
23 the Hamming ball has 2,048 words and the code is perfect. At 24 the ball has
2,325, and the packing misses by **7,254,016** words — a deficit of `1771/4096`
of the space. The extension raises the distance from 7 to 8, which buys
detection and never correction.

### 2.4 The totient sub-cycle count

Checked by traversal against the closed form for every `N` from 3 to 200 —
**198 lengths, 0 disagreements**. The corollary holds on the same range: the
count is zero exactly at the primes, with no failures. The first zeros are
`3, 5, 7, 11, 13, 17, 19, 23, 29`; the composite counts rise irregularly
(`C(24) = 8`, `C(30) = 11`, `C(60) = 22`).

### 2.5 Steiner — `S(5, 8, 24)` by enumeration

All `C(24,5) = 42,504` five-sets covered, each by exactly one octad
(`multiplicities == (1,)`), and `759 × C(8,5) = 42,504` accounts for them with
nothing left over. Two distinct octads meet in at most 4 points, and every
four-set lies in exactly 5 octads.

### 2.6 The dimension carrier

`m c⁴` and `m c²` differ as dimension vectors — `(1,4,−4,0,0,0,0)` against
`(1,2,−2,0,0,0,0)` — and are **indistinguishable under XOR**, because XOR is
blind to even shifts. That is the whole argument that meaning is primary and
the bit pattern is a carrier. The base-9 box `[−4,4]⁷` has `9⁷ = 4,782,969`
points, fits inside 24 bits with 11,994,247 to spare, and neither an eighth
dimension nor a ninth exponent fits.

### 2.7 The extraspecial count

The plus-type formula is checked against enumeration for ranks 1 to 6 and
matches. At rank 12: 8,390,656 singular classes, 8,386,560 non-singular, and a
group of order `2²⁵ = 33,554,432` with 16,781,312 involutions-or-identity —
which is the plus-type count again, independently.

### 2.8 The Platonic angle totals

| solid | face-angle total |
|---|---|
| tetrahedron | 720° |
| octahedron | 1440° |
| cube | 2160° |
| icosahedron | 3600° |
| dodecahedron | 6480° |

All five are multiples of 144°, and they total 14,400° = 80π radians. The
pattern is Descartes' total angular defect read forwards: the total is
`360V − 720`, so it is a multiple of 144 exactly when `V` is even — which it is
for all five. There is nothing Platonic about the 144.

### 2.9 Literal Data Physics

All 4,096 cosets walked. 4,095 are excited and **all 4,095 descend**; the
descent is not a search, because `H = [B | I₁₂]` makes coordinate `12 + j`
toggle syndrome bit `j` and nothing else, and the named flips match the energy
in every case. Maximum energy 12. The mass defect is 12, which is exactly the
bound the minimum weight forces. Allowed weights `{0, 8, 12, 16, 24}` with no
forbidden weight present, so the forbidden zone is real, and parity is conserved
on octad pairs.

### 2.10 The triad census

Of the 759 octads, **44** score a perfect 1 on the archive's 3-axis measure and
715 do not. The deviation census is `0: 44, 2: 336, 4: 312, 6: 58, 8: 9` — every
deviation even, every triad sum even, maximum 16, which is the bound. The two
archive scores are irrational; recomputed as brackets, the class-A score lies in
`[1562500/4870943, 12500000/38967543]` and the class-C score in
`[3125000/13050329, 25000000/104402629]`, each agreeing with the archive's
decimal to five places. The 44 are real. The "3-6-9" that names them is not:
any three-element set gives 3, 6 and 9, and the six faces are three symmetric
operations counted twice.

---

## 3. What the audit adds that the Lean does not

| check | why the Lean cannot do it |
|---|---|
| the enumerator agrees with **this** package's code | the Lean theorem is about a code with the right weights; the audit fixes which code |
| `c` recovered for 20 anchors | the Lean proves the algebraic identity; the audit shows the shipped constants instantiate it |
| 198 polygon lengths traversed | the Lean proves the closed form; the audit walks the orbits and compares |
| 42,504 five-sets covered | the Lean proves the design property; the audit enumerates the design |
| brackets on the two irrational scores | the Lean states the inequality; the audit produces the rationals that witness it |

---

## 4. Three corrections to the archive

1. **The LDP mean energy is exactly 6.** The archive reports 6.05 from a sample
   (`121/20`). Averaged over all 4,096 cosets the mean is `6` exactly. The
   archive's figure was sampling error, and the exact value is the cleaner
   statement. The sampled relaxation-step count `381/100` is recorded beside it
   for the same reason.
2. **`24` is not forced by perfection.** The archive's first-principles study
   treats length 24 as structurally necessary. It is not: 7 and 23 are the only
   perfect lengths, and 24 is selected by self-duality, which is a symmetry
   preference and a good one — but a different argument.
3. **The totient sub-cycle "theorem" is Euler's totient.** The count is real and
   the primality corollary holds, but the derivation costs a factorisation, so
   it is not a cheap primality test. The geometry does derive primality; it
   derives it the expensive way.

---

## 5. Where this sits

* Lean half: [`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md).
* Second pass over the same archive:
  [`SOURCE_SALVAGE_SECOND_PASS.md`](SOURCE_SALVAGE_SECOND_PASS.md).
* The layer-by-layer dive that follows a single claim down:
  [`ARCHIVE_DEEP_DIVE_STUDY.md`](ARCHIVE_DEEP_DIVE_STUDY.md).
* The exactness the audit is held to: D7 and D9 of
  [`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md).
