# The Geometric Language Machine (GLM)

A substrate-native codec and exact reasoner for dimensional knowledge, built on
the extended binary Golay code `[24,12,8]`, the Miracle Octad Generator (MOG),
the hexacode over GF(4), and the free abelian group `(Z^7, +)` of SI dimension
exponents — with optional geometric and Leech/Griess layers on top.

Standard library only — no third-party dependencies, Python 3.8+.

## The state and its view

| layer | lives in | role |
|---|---|---|
| **meaning** — the state | `(Z^7, +)` — exponents of L, M, T, I, Θ, N, J | the only thing a concept *is*; decides admissibility, derivations, conversions |
| **carrier** — a derived view | `F_2^24` — Golay codewords, MOG columns, hexacode shadows | a pure function of the meaning; gives locality, snap distance, lawfulness, geometry |

The arrow points one way. A `Concept` is a frozen record whose only fields are
a name, a `Dimension`, a symbol and a unit; `carrier`, `shadow`, `snap`,
`lawful`, `tax` and `nrci` are read-only properties computed by the pure
function `derive_substrate(dim)` and cached, nothing more. A bit pattern is
never an input, and there is no setter that could give a concept a word its
meaning does not produce — `Concept.carrier_is_derived()` re-derives and checks
it. Paper section 5 gives the reason: an `F_2` carrier composed by XOR cannot
be injective on `Z^7`, so it cannot be the object that means something, while
the integer vector can (`GLM.no_injective_additive_into_char_two`,
`GLM.f2_carrier_cannot_be_primary`, both machine-checked).

Composition of quantities is addition in `Z^7`; equation checking is integer
equality; target synthesis is an integer linear system solved by Smith normal
form; dimensionless-group analysis is the kernel of the same matrix. No
verdict anywhere reduces an exponent modulo 2 — the mod-2 ceiling is measured
in an appendix (`glm_metrology.py` section 6, `REASONER.mod2_ceiling_batch`)
as a negative result about the rejected design, not consulted as a second
opinion.

## Files

| file | what it is |
|---|---|
| `glm_paper.py` | **the paper**: the full write-up in the module docstring, plus an operational run that verifies all 43 numbered claims and writes `results/glm_results.json` |
| `glm_reasoner.py` | **the companion implementation**: concepts, equation audit, target synthesis, Buckingham-Pi, geometry telemetry, scene export, CLI |
| `glm_substrate.py` | Golay code, hexacode, MOG alignment, Leech metrics |
| `glm_codec.py` | the column bijection, the 24-bit codec, the `Z^7` carrier |
| `glm_metrology.py` | **the meaning layer**: `(Z^7,+)`, 90 named quantities, the expression parser, equation auditing; section 6 is the appendix holding the rejected `F_2` carrier |
| `glm_linalg.py` | exact integer linear algebra (Smith normal form, kernels, solving) |
| `glm_geometry.py` | the fibre geometry: `Z_4` versors, integer quaternions, walks, winding, holonomy, conformal grading, vacua, colour |
| `glm_moonshine.py` | the Leech/Griess bookkeeping: line census, `24 × 4096` indexing, the 196,884 ledger, the eta series, the 300-dimensional Jordan algebra |
| `glm_m24.py` | the automorphism search, Schreier–Sims stabiliser chains, and `Aut(Golay) = M24` computed rather than quoted |
| `glm_monster.py` | optional upper tiers: code automorphisms, `2^(1+24)` in 4096D, the normaliser `2^(1+24) : S_12`, the snap algebra |
| `test_glm.py` | 165 tests across all modules |
| `DEVELOPMENT_CATALOG.md` | version-by-version notes on the 21 archived GLM files plus an idea-by-idea map of what shipped, what was corrected, and what was dropped |
| `../RequestProject/GLM.lean` | machine-checked proofs of the paper's structural propositions (Lean 4 + Mathlib) |

Every module runs standalone and prints its own audit.

## Running it

```bash
python3 glm_paper.py            # the paper's full verification run (~15 s, 43 claims)
python3 glm_paper.py --quick    # skips the exhaustive sweeps
python3 glm_reasoner.py         # the companion's demonstration suite
python3 test_glm.py             # the test suite (~40 s, 165 tests)

python3 glm_substrate.py        # substrate self-audit
python3 glm_codec.py            # codec self-audit
python3 glm_metrology.py        # metrology self-audit
python3 glm_geometry.py         # fibre-geometry self-audit
python3 glm_moonshine.py        # Leech/Griess ledger audit
python3 glm_m24.py              # builds Aut(Golay) = M24 and proves it is all of it
python3 glm_monster.py          # upper-tier audit
```

Command line of the companion:

```bash
python3 glm_reasoner.py check "energy" "mass*speed^2"
python3 glm_reasoner.py check "energy" "mass*speed^4"      # rejected in Z^7
python3 glm_reasoner.py solve energy mass speed            # energy = mass * speed^2
python3 glm_reasoner.py solve speed energy mass            # fractional powers: sqrt(E/m)
python3 glm_reasoner.py pi force density speed length      # dimensionless groups
python3 glm_reasoner.py show energy                        # full substrate telemetry
python3 glm_reasoner.py colour energy                      # hex colour and snapped colour
python3 glm_reasoner.py walk energy mass speed energy      # versor walk and winding number
python3 glm_reasoner.py holonomy energy mass speed         # Q8 holonomy of the loop
python3 glm_reasoner.py symmetry energy                    # the M24 orbit of a carrier word
python3 glm_reasoner.py m24                                # Aut(Golay) = M24, computed
python3 glm_reasoner.py ledger                             # the 196,884 dimension ledger
python3 glm_reasoner.py list                               # the quantity library
```

## Library usage

```python
from glm_metrology import Dimension
from glm_reasoner import REASONER

REASONER.audit("energy", "mass*speed^4")["accepted"]              # False, in Z^7
REASONER.concept("energy").carrier_is_derived()                   # True: the bits are f(meaning)
REASONER.concept("energy").with_meaning(Dimension((4,1,-4,0,0,0,0)))  # new meaning, new bits
REASONER.mod2_ceiling_batch([("energy", "mass*speed^4", "E = mc^4")])  # appendix: what F_2 would have said
REASONER.solve("power", ["current", "resistance"]).formula()      # power = current^2 * resistance
REASONER.pi_groups(["speed", "length", "kinematic_viscosity"])    # 1/Re
REASONER.concept("energy").telemetry()                            # carrier, shadow, snap, cost, geometry
REASONER.walk(["energy", "mass", "speed", "energy"])              # winding of a closed walk
REASONER.holonomy(["energy", "mass", "speed"])                    # ordered product of fibre quaternions
REASONER.symmetry_orbit("energy")                                 # M24 orbit: 2,024 words of weight 3
```

## What the run establishes

* the Golay substrate: 4096 codewords, `d = 8`, self-dual, doubly even, weight
  enumerator `1 + 759z^8 + 2576z^12 + 759z^16 + z^24`, 759 octads, covering
  radius 4 with leader profile `1/24/276/2024/1771`, and a genuine six-way tie
  at distance 4 (reported, not hidden);
* the MOG alignment sends all 4096 codewords to hexacode words (0 failures),
  and each GF(4) label has exactly 4 columns above it;
* the codec `F_2^24 <-> GF(4)^6 x Z_4^6` is a bijection, and the chain
  `Z^7 -> bits -> shadow -> bits -> Z^7` loses 0 bits for all 90 quantities;
* the architecture invariant, checked over the whole library and over a sweep
  of the exponent box: every concept's word is `derive_substrate(dim).word`,
  distinct meanings give distinct words, the derived fields cannot be
  assigned, and XOR of two words is not the word of the product — [Claims C42,
  C43], `TestCarrierIsDerived`;
* the mod-2 ceiling, as an appendix measurement, in three independent forms:
  of the 2,346 distinct
  dimension pairs in the library, 101 are indistinguishable to any XOR-based
  checker; of the 1,260 false equations obtained by shifting one exponent of a
  named quantity by ±2, a mod-2 checker accepts all 1,260 (96 of them are
  traps a user could write, `E = mc^4` among them); and over the whole
  exponent box `[-2,2]^7` exactly 31,335,196 of 3,051,718,750 pairs (1.03%)
  collapse mod 2. `(Z^7,+)` separates every one of them, and the named traps
  (`E = mc^4`, `F = ma^3`, `E_v = Φ_v·A`, `σ = E_e/Θ^2`) are rejected;
* the reasoner reproduces known derivations, returns fractional powers where
  they are required (`v = sqrt(E/m)`), and says "no pathway" where there is
  none;
* the fibre geometry: the fibre key is a quarter turn in `Z_4`, closed walks
  wind by an integer number of full turns, holonomy is a genuinely
  path-dependent element of `Q8` that telescopes exactly against the reversed
  loop, the conformal grading is `sigma/2`, and the colour codec round trips;
* the automorphism group of the code is *built*, not quoted: a matroid-based
  search produces automorphisms, a Schreier–Sims stabiliser chain gives a
  5-transitive group of order 244,823,040 that is transitive on the 759 octads
  (stabiliser 322,560), the 2576 dodecads (stabiliser 95,040 = `|M12|`) and the
  1771 sextets (stabiliser 138,240), and an exhaustive enumeration of the 48
  automorphisms fixing five coordinates shows by orbit–stabiliser that this
  group is all of `Aut(C)` — i.e. `M24`. It preserves every substrate decision about a carrier
  word (weight, lawfulness, snap distance) but not the syndrome, which is read
  off a fixed basis;
* the extraspecial group `2^(1+24)` satisfies all its defining relations as
  exact operator identities in 4096 dimensions, while the 24-dimensional
  action does not (checked, not assumed); the normaliser `2^(1+24) : S_12`
  acts on the 4096-dimensional space by a verified homomorphism;
* the Leech ledger: the 196,560 minimal vectors form 98,280 antipodal lines
  (split `552 + 48,576 + 49,152`), class C is indexed bijectively by
  `24 × 4096 = 98,304`, and `1 + 299 + 98,280 + 98,304 = 196,884 = 324 +
  196,560` is confirmed against an exactly computed eta/`j` head; the
  300-dimensional Jordan algebra `R ⊕ S²₀(R^24)` is commutative, unital,
  non-associative, and satisfies the Jordan identity.

## What is proved rather than measured

`../RequestProject/GLM.lean` (Lean 4 with Mathlib, no `sorry`, no added
axioms) carries the paper's structural propositions:

* `GLM.xor_blind` — any additive encoder into a group where `m + m = 0`
  satisfies `f (d + 2u) = f d`: the mod-2 ceiling;
* `GLM.no_injective_additive_into_char_two` — no such encoder is injective on
  `Z^7`, so an `F_2` carrier cannot be the state (Corollary 1 of section 5.3);
* `GLM.f2_carrier_cannot_be_primary` — the same statement in the form the
  architecture uses: any XOR-composing carrier identifies two genuinely
  different meanings, whatever the encoding;
* `GLM.digits`, `GLM.digits_injOn` — the derivation in the other direction is
  injective, so the bits really are a faithful view of the integer vector;
* `GLM.mc4_eq`, `GLM.mc4_ne`, `GLM.mc4_indistinguishable_under_xor` — every
  XOR encoder accepts `E = mc^4`, which `(Z^7,+)` rejects;
* `GLM.xor_universal_kernel` — two dimensions are confusable by some XOR
  encoder exactly when they agree mod 2, so the ceiling is precisely a mod-2
  effect and nothing more;
* `GLM.carrier_card`, `carrier_fits_24_bits`, `carrier_embeds`,
  `zigzag_lt_nine`, `zigzag_injOn` — the base-9 carrier's capacity
  `9^7 = 4,782,969 < 2^24` and the injectivity of its digit map;
* `GLM.colLabel_table`, `colLabel_xor`, `fibre_card`, `fibres_partition` —
  the column-label map is `F_2`-linear and exactly 4-to-1 on the 16 states;
* `GLM.winding_integral`, `GLM.winding_integral_liftStep` — Proposition 2 of
  section 9.3: on a closed walk the lifted `Z_4` steps sum to a multiple of 4,
  for an arbitrary lift and for the concrete `{-1,0,1,2}` lift used here;
* `GLM.shift_sign_comm`, `GLM.shift_sign_anticomm`,
  `GLM.shift_sign_comm_off_diag` — the Schrödinger relations of section 8.2:
  `X_b Y_a = (-1)^<a,b> Y_a X_b`, anticommuting exactly on the diagonal, which
  is the extraspecial commutator `[x_i, y_i] = z`;
* `GLM.mathieu_order_arithmetic` — the orbit–stabiliser arithmetic behind
  `24 × 23 × 22 × 21 × 20 × 48 = 759 × 322,560 = 244,823,040`;
* `GLM.dimension_ledger` — the arithmetic of section 10.

Everything else in the paper is a finite verification, run by `glm_paper.py`.

## Corrections to earlier versions

The nineteen archived iterations are read one by one in
`DEVELOPMENT_CATALOG.md`; one gap they all left open — `M24` named but never
constructed — is closed in `glm_m24.py`. Six of their claims did not survive
checking, and
the paper states each correction where the corresponding result is used:

1. **The four-tier encoder was many-to-one** (section 3.2). Its reported
   "0-bit reconstruction error" described the feature bits, not the concept,
   and the published version also skipped the amount-of-substance exponent. It
   is replaced by a bijective base-9 carrier on `[-4,4]^7`; the tiers survive
   as an interpretive view (`ontological_profile`).
2. **The "snap-based Griess product" is associative** (section 8.3).
   Substituting `snap(v) = v xor L(sigma(v))` collapses it to
   `v . w = snap(v) xor snap(w)`, which is commutative *and* associative, with
   all triple defects vanishing. It is the retraction of `F_2^24` onto
   `(C, xor)` induced by the decoder — not a Griess-like algebra, and the
   Monster does not enter. A layer that really is commutative, unital and
   non-associative is supplied instead in section 10.4.
3. **`L0` was the grading in disguise** (section 9.5). The archive's "H^6
   norm" is constant (always 6), and its `L0` equals `sigma/2`, where `sigma`
   is the number of nonzero GF(4) column labels. It is reported as such.
4. **The archive's "Leech inner product" was a Hamming distance** (section
   10.5): the quantity computed is `24 - 2 d_H`, a function of the shadow
   alone, not an inner product of Leech vectors.
5. **The outer factor is `S_12`, not `Co_1`** (section 10.6). The group built
   in v19 is the semidirect product `2^(1+24) : S_12` acting on 4096
   dimensions; that is what is verified, and that is what it is called.
6. **The McKay–Thompson tables and the "concept → Monster conjugacy class"
   map are dropped** (sections 10.3 and 11). The tabulated character values in
   the archive are unsourced and mutually inconsistent; the class assignment
   was a relabelling of the syndrome. Only the exactly computed head of `j`
   (196,884 = 324 + 196,560) is retained.

A seventh change is one of evidence rather than of substance: earlier drafts
quoted "100% precision versus 89% for the mod-2 substrate over 6,793 equation
pairs" without a reproducible definition of that population, and no code in the
archive generated it. The claim itself is right — and is now a theorem, above —
so it is restated with denominators anyone can regenerate: the library pair
census, the ±2 perturbation family, and the exponent-box count listed under
"What the run establishes".

## Extending it

The invariants any change must preserve are listed in `glm_paper.py`
section 13 (I0–I7) and enforced by `test_glm.py`. The shortest useful
contributions: more quantities and aliases (`QUANTITIES` in
`glm_metrology.py`, one line each), a numeric-value layer on top of the
dimensional one, and a named-relation store so synthesis can return the actual
law rather than only the dimensionally admissible product.
