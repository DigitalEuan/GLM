# `glm_universal.data_objects` — typed carriers over the substrate

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

**Status: implemented (Step 2), extended since.** Eight domains, one carrier
shape: every object here is a point of $\mathbb{Q}^{24}$ with an exact 2-adic
digit stack behind it.

As loaded by the runtime (`GeometricSession.register`), the registers are
physics **726**, chemistry **118**, **51 molecules**, mathematics **22**,
lexicon **95** (the semantic lexicon), spatial **28**, harmonics **28**,
economics **21** — 1,089 carriers in all.
The live counts are recomputed in [`../../FIGURES.md`](../../FIGURES.md) under
*Registers*; `spatial` is built in the runtime rather than here. The tables
below record the *verification sweep* over the frozen snapshots at the time it
was run, and give the register sizes of that run; the sizes above are the
current ones.

All figures below were computed by
`workflow/08_step2_data_objects_verification.py` and are recorded in
`results/step2_data_objects_verification.json`. They are not quoted from
anywhere.

---

## 1. The losslessness contract has two legs

A codec is only lossless if **both** of these hold, and the distinction is the
reason this package tests what it does:

| Leg | Statement | Whose property |
|---|---|---|
| substrate | `class_stack_rebuild(class_stack(v)) == v` | the digit stack |
| semantic | `decode(encode(x)) == x` | the codec |

The first can hold while the second fails. A codec that silently drops a field
still produces a perfectly faithful stack — *of the truncated carrier*. Any
claim of losslessness that checks only the substrate leg is worth nothing, so
`Codec.check()` asserts both and every domain sweep reports them separately.

Measured, this run:

| Domain | Objects | Substrate leg | Semantic leg |
|---|---|---|---|
| physics | 660 | 660/660 | 660/660 |
| chemistry | 118 | 118/118 | 118/118 |
| mathematics | 22 | 22/22 | 22/22 |
| lexicon | 10 | 10/10 | 10/10 |

---

## 2. Dynamic stack derivation

Three quantities are easy to conflate, so they are named apart.

**`denominator`** — the least common denominator of the 24 rational
coordinates. Clearing it makes the carrier integral. It is a *general* integer.

**`dyadic_exponent`** — the least $S \ge 0$ with $2^S v \in \mathbb{Z}^{24}$.
This is what the plan text calls the offset $O$. It exists **only when every
denominator is a power of two**, and is therefore `None` for most real data:
the physics register uses denominators of 3 and 12, and hydrogen's density
$2247/25{,}000{,}000$ has denominator $2.5 \times 10^7$. The package reports it
for completeness and **does not rely on it** — the general LCD route always
exists and is what the codecs use. This is a deliberate, documented departure
from the plan's phrasing; a purely dyadic rescaling cannot encode this data,
and `test_dyadic_exponent_absent_for_the_physics_register` pins that fact down.

**`offset` (translation) and `depth`** — the substrate's own parameters. With
$m = \max|\text{cleared coordinate}|$, the offset is the least power of two
$O \ge m$ and the depth is the least $D$ with $2^D > O + m$. Every shifted
coordinate then lies in $[0, 2^D - 1]$ inclusive, which is the containment the
plan requires; `StackParameters.contains()` checks it and
`derive_dynamic_parameters` raises if it ever fails.

### No hardcoded ceiling

The module default `STACK_DEPTH = 10` is *not* used on the codec path. Measured
depths, each verified to be the least admissible (one plane fewer raises):

| Carrier | Denominator | Depth | Dyadic $S$ |
|---|---|---|---|
| zero vector | 1 | 1 | 0 |
| integers $-12 \ldots 11$ | 1 | 5 | 0 |
| Leech minimal vector | 1 | 4 | 0 |
| $3/4$ throughout | 4 | 3 | 2 |
| $1/3$ throughout | 3 | 2 | — |
| $1/12$ throughout (physics lattice) | 12 | 2 | — |
| **hydrogen, full element carrier** | 25,000,000 | **39** | — |
| $\pm 10^{18}$ | 1 | 61 | 0 |
| $10^{40}$ | 1 | **134** | 0 |
| $10^{-30}$ | $10^{30}$ | 2 | — |
| $10^{25}$ and $10^{-25}$ together | $10^{25}$ | **168** | — |

Depth over the element register runs **24 to 41**; over the physics register,
**2 to 7**. A fixed depth of ten would fail on every element, which is why
`test_module_default_depth_is_insufficient_for_chemistry` asserts that the
fixed-depth call *raises* while the dynamic one round-trips. That test breaks
if anyone reintroduces a constant.

---

## 3. Physics — 660 quantities, SI7 and EXT10

Ingested from `glm2_library.CONCEPTS` and frozen into `_data/physics_660.json`
as exact rationals. EXT10 axes:

$$(L, M, T, I, \Theta, N, J, A, S, B)$$

SI7 is the first seven. EXT10 adds plane angle $A$, solid angle $S$ and
information $B$, which SI treats as dimensionless.

### Layout (10 + 7 + 7 = 24, no padding)

| Coords | Content |
|---|---|
| 0–9 | EXT10 exponents $L\,M\,T\,I\,\Theta\,N\,J\,A\,S\,B$ (exact, may be fractional) |
| 10–16 | SI7 projection (redundant by construction) |
| 17–23 | `scale`, `rank`, `p`, `t`, `c`, `kind`, `domain` |

Coordinates 10–16 duplicate 0–6 deliberately: both bases live in one carrier,
and the redundancy gives the decoder a consistency check. A tampered SI7 slice
raises rather than decoding to a plausible wrong answer
(`test_internally_inconsistent_carrier_is_rejected`).

### What SI7 costs, measured over the register

| Basis | Distinct dimension vectors | Colliding pairs |
|---|---|---|
| SI7 | 131 | 14,245 |
| EXT10 | 155 | 11,227 |

**EXT10 resolves 3,018 concept pairs that SI7 leaves colliding.** 60 of the 660
concepts have a nonzero $A$, $S$ or $B$ exponent — those are exactly the ones
the projection loses. The canonical case: torque is $L^2 M T^{-2} A^{-1}$ and
energy is $L^2 M T^{-2}$; identical in SI7, distinct in EXT10.

Six concepts carry fractional exponents (`fracture_toughness`,
`stress_intensity`, `thermal_effusivity`, `wavefunction_3d`,
`voltage_noise_density`, `current_noise_density`) and survive the round trip as
`Fraction`, not as decimals.

```python
from glm_universal import data_objects as do

q = do.quantity_by_name("torque")
q.dimension_string("EXT10")      # 'L^2 M T^-2 A^-1'
q.dimension_string("SI7")        # 'L^2 M T^-2'
do.si7_projection_lossy(q)       # True

obj = do.PhysicsCodec().check(q)      # asserts both round-trip legs
obj.coordinate("ext10.A")             # -1
obj.parameters().depth                # 4
```

---

## 4. Chemistry — all 118 elements

Ingested from PubChem's periodic table into `_data/elements_118.json`. Every
decimal column was converted with `Fraction(str)`, which is **exact**:
hydrogen's atomic weight is the rational $126/125$, not `1.008` rounded to a
binary float.

### Missingness is data, not an inconvenience

The source is a real measured table and it has holes. In-repo coverage:

| Field | Coverage |
|---|---|
| atomic weight, group block, standard state, period | 118/118 |
| valence electrons (**derived**, see below) | 108/118 |
| melting point | 103/118 |
| ionization energy | 102/118 |
| atomic radius (PubChem) | 99/118 |
| density | 96/118 |
| electronegativity (Pauling) | 95/118 |
| boiling point | 93/118 |
| electron affinity | 57/118 |
| **covalent radius (Cordero)** | **24/118** |
| **homonuclear BDE** | **21/118** |

**Nothing is imputed.** A missing field is coordinate `0` *and* has its bit set
in the missingness mask at coordinate 17, so a measured zero and an absent
measurement stay distinguishable and the round trip restores `None` rather than
a fabricated zero. All **395 missing fields across the register** were restored
as `None` this run. Any analysis that reads the carrier without reading the
mask is reading 395 fabricated zeros.

The covalent-radius and BDE columns are sparse because those are the only
values present in the session's own sources; they were not topped up from
memory. Consumers needing full coverage must supply a cited table.

Valence electrons are **derived**, not quoted: the $s$ and $p$ electrons of the
highest principal quantum number in the PubChem electron configuration. For the
ten elements whose configuration is flagged `(predicted)` the derivation is
declined and the field is missing.

### Layout

| Coords | Content |
|---|---|
| 0 | `z` |
| 1–16 | the 16 measured/derived fields, in `MEASURED_FIELDS` order |
| 17 | missingness bitmask over coordinates 1–16 |
| 18–23 | Golay address: codeword, three brick weights, hexacode shadow, total weight |

### The Golay address

$z$ indexes the $[24, 12, 8]$ code's 4096 codewords directly. Over all
$\binom{118}{2} = 6903$ pairs the **minimum Hamming separation is 8** — exactly
the code's minimum distance, and all 118 addresses are distinct codewords. The
periodic table inherits an error-correcting separation it did not have. A
corrupted address is detected on decode, not believed
(`test_corrupted_golay_address_is_rejected`).

```python
h = do.element_by_symbol("H")
h.atomic_weight_u                     # Fraction(126, 125) — exact
obj = do.ElementCodec().check(h)
obj.parameters().depth                # 39, forced by the density denominator
do.element_by_symbol("Og").electronegativity_pauling   # None, not 0
```

A companion register of **52 diatomic species** with experimental $D_0$ values
at 0 K (NIST CCCBDB) is available via `load_diatomic_register()`.

---

## 4b. Molecules — 51 species, nothing tabulated but the formula

`molecules.py` is the multi-carrier register. It answers the question the
element register could not: how to say `C6H12O6` to the machine.

**A molecule is held twice, because one holding cannot do both jobs.**

| Holding | What it is | What it is good for |
|---|---|---|
| bundle | `((symbol, count, carrier), ...)` — one element carrier per distinct element, with its multiplicity | *faithful*: `formula_from_bundle` reads the formula straight back off it |
| composite | one point of $\mathbb{Q}^{24}$ derived from the bundle | the geometry: distance, nearest, clustering |

The composite is a **summary**, so it might collide. `composite_collisions`
looks for two molecules sharing one composite and reports what it finds rather
than assuming injectivity; measured over the register, all **51 composites and
all 51 bundles are distinct — 0 collisions of either kind**.

**Nothing is stored but a name and a formula.** All 19 derived fields —
`atom_count`, `distinct_elements`, `molar_mass_u`, `electron_count`,
`valence_electron_total`, `heaviest_z`, `lightest_z`, the four
electronegativity fields, `degree_of_unsaturation`, `charge`, the C/H/O/N
counts, `heteroatom_count`, `carbon_mass_fraction` — are computed from the
element register when the carrier is built. Where the element register has a
gap the value is *absent* and the missingness bit is set, exactly as for an
element: `degree_of_unsaturation` is missing for 14 of the 51, and nothing is
imputed.

Layout: the 19 derived fields at coordinates 0–18, then `missing_mask` and the
three composition bricks with their Golay codeword at 19–23.

The formula grammar (`parse_formula`) reads counts, nested brackets, hydrates
written with `.`, and a trailing charge: `H2O`, `Ca(OH)2`, `Fe2(SO4)3`,
`CuSO4.5H2O`, `SO4 2-`. An unknown symbol is refused by name, never silently
dropped. The register spans 17 distinct elements and includes 5 ions; the
heaviest species is iron(III) sulfate at $199939/500$ u and the largest by atom
count is sucrose at 45 atoms.

```python
objs, codec = do.molecule_objects()
do.formula_from_bundle(do.molecule_bundle(do.molecule_by_name("glucose")))
```

See `report molecules` for the whole thing recomputed on demand, and
`report chemistry coverage` for how sparse the element data underneath it is.

---

## 4c. Harmonics — 28 intervals, and no float anywhere

`harmonics.py` is the newest register, and the cheapest one to justify: an
interval *is* a ratio of two positive integers, so nothing about it has to be
measured, calibrated or rounded. All 24 coordinates of `HARMONIC_LAYOUT` are
computed from the pair `(n, d)` in lowest terms — the exponents over 2, 3, 5
and 7, Tenney height `n · d`, Euler's gradus suavitatis, the nearest
equal-tempered step and the exact rational `(n/d)^12 / 2^k` by which that step
misses — and only `n` and `d` are needed to read the interval back, which is
what makes `IntervalCodec`'s round trip exact.

The register holds **28 intervals**: 18 just, 5 septimal and 5 commas, over
prime limits 2, 3, 5 and 7. The nearest equal step is decided by comparing
`r^24` against powers of two — integers, not logarithms — so `tet_error` is an
exact `Fraction`, `531441/524288` at the fifth and `244140625/268435456` at the
just major third.

The register exists to make a claim testable rather than to enlarge the
package: `reasoning/harmony.py` runs the catalogue's universality sentence
against it, and `RequestProject/GLM/Harmony.lean` proves the reason every
tempering error is non-zero.

---

## 5. Mathematics

`RationalMatrix` — any $r \times c$ over $\mathbb{Q}$ with $rc \le 24$,
row-major, zero-padded tail. The shape travels in the attributes, so a
$2 \times 5$ and a $5 \times 2$ with identical entries share a carrier but
decode to different objects. The eight shapes that fill the carrier exactly are
$1{\times}24$, $2{\times}12$, $3{\times}8$, $4{\times}6$, $6{\times}4$,
$8{\times}3$, $12{\times}2$, $24{\times}1$; $4 \times 6$ is the MOG frame
itself.

`Reflection` — $x \mapsto x - 2\frac{\langle x, r\rangle}{\langle r, r\rangle} r$,
exact over $\mathbb{Q}$. Applying it twice returns the input **identically**,
not to within rounding — asserted for integral, unit and $1/3$-valued roots.
`is_2a_axis()` returns `False` for non-lattice roots rather than raising, and
`True` for Leech minimal vectors (norm² 32).

`FieldElement` — $\mathrm{GF}(2)^{24}$ or $\mathrm{GF}(4)^6$, with membership
in the Golay code and the hexacode reported rather than assumed.

---

## 6. Lexicon

The tempting way to put a word in a vector is to hash it. Hashing is not
invertible, so a hashed carrier cannot be decoded and a losslessness claim over
one is false by construction. Worse, Python's `hash` on `str` is salted
per process, so a hashed embedding would not even be *deterministic across
runs* — silently violating the package's no-randomness invariant.

So this module **interns**. A `Vocabulary` assigns each token a stable index in
first-registration order; the carrier stores indices; decoding looks them back
up. `test_no_hashing_is_used` greps the module to keep it that way.

Layout: subject, part-of-speech, arity, three feature slots, feature mask,
eight predicate indices, eight object indices, and a checksum at coordinate 23
that catches perturbed indices instead of letting them resolve to different
words.

Eight relations is a real ceiling, and a ninth **raises** rather than being
truncated. A truncating encoder would still pass a substrate round-trip test
while losing the ninth relation — precisely the failure the two-legged contract
exists to catch.

```python
objs, codec = do.lexicon_objects()   # codec carries the vocabulary
codec.decode(objs[0])                # Concept('electron', 'noun', ...)
```

---

## 6b. Comparison classes — 45 brackets, 11 scales, 64 degree words

`hot` is a lexicon concept, and the concept cannot say *how hot*, because hot
for a cup of tea is 363 K and hot for a stellar surface is 44 000 K. What is
missing is the **comparison class** the word is measured against, and
`comparison_classes.py` is the register of them: **45 classes over 11
quantities** (temperature 6, length 5, mass 5, velocity 5, volume 5, density 4,
illuminance 4, force 3, luminous intensity 3, pressure 3, frequency 2), each an
exact bracket `[low, high]` in the SI base unit of its quantity with a typical
magnitude inside it. Seven further names are aliases resolving to one of the
eleven — `size` → `volume`, `light` → `illuminance`, `distance` → `length` and
so on — and supply no coordinate of their own.

Nothing dimensional is typed twice. A class names a quantity, and the unit,
the dimension and the ten EXT10 exponents of its 24-coordinate carrier are read
out of the physics register at load time — a class naming a quantity the
register does not hold **fails to load**, which is the same derivation rule the
molecules register follows.

Beside the classes are **11 measure scales carrying 64 degree words**, each at an
exact position in `[0, 1]`, and `lexicon_agreement()` checks the 12 words the
scales share with the semantic lexicon: the quantity must be the one the
concept's `property_of` relation names, the position must fall on the side of
the midpoint the `positive_negative` primitive says, and an `opposite_of` pair
must have positions summing to 1. It reports `agrees: True`, with `heavy`
noted as the one word whose polarity is the neutral `1/2` — a case the static
reading cannot place and the scale can.

```python
klass = do.class_by_name("tea")
klass.magnitude_at(Fraction(7, 8))    # Fraction(363, 1) — hot, in kelvin
```

The reading built on this register, the audit that shows adding it gives
nothing up, and the query that refuses where the registers hold nothing are in
`reasoning/measure_view.py` and
[`../../../studies/RELATIVE_MEASURE_STUDY.md`](../../../studies/RELATIVE_MEASURE_STUDY.md).

---

## 6c. Denotations — 36 decisions about what a name denotes

Repairing the lexicon's `related_to` triples leaves 39 that the physics
register cannot decide, and 38 of those decline because an endpoint *reaches no
dimension the register holds*. That sentence reports a lookup, not a fact about
the word: it cannot tell a name the register merely spells differently from a
name that denotes no magnitude at all.

`denotation.py` is the register that settles the difference — **36 entries**,
one per undimensioned endpoint, each a judgement made on purpose and written
down with its justification. There are six verdicts and only the first makes a
name dimensional:

| verdict | entries | example |
|---|---|---|
| `quantity` | 1 | *gravity* — the register's `gravitational_field` under an ordinary-language name |
| `ambiguous` | 3 | *motion* — velocity, momentum or kinetic energy, and the word does not choose |
| `polymorphic` | 4 | *magnitude* — takes the dimension of whatever it is applied to |
| `carrier` | 9 | *electron* — bears a mass and a charge and is neither |
| `process` | 11 | *rotate* — quantified by an angle, and not one |
| `abstraction` | 8 | *equilibrium* — a condition over quantities, taking no value |

A `quantity` verdict supplies **no coordinate**: the dimension continues to be
read out of the physics register, so a denotation can no more invent a quantity
than an alias can. `denotation_audit()` refuses a verdict outside the six, a
`quantity` naming something the register does not hold, an `ambiguous` entry
with fewer than two real candidates, a name that shadows a registered quantity
or an existing alias, an entry with no justification, and any duplicate
(`sound: True`).

```python
do.verdict_of("motion")                 # 'ambiguous'
do.denotes_quantity("gravity")          # 'gravitational_field'
do.denotes_quantity("cause")            # None — decided, not missing
```

What the decisions change is measured next door, in
`reasoning/denotation_view.py`, and written up in
[`../../../studies/DENOTATION_STUDY.md`](../../../studies/DENOTATION_STUDY.md).

---

## 7. Exactness

`float` is refused at construction by `as_exact()`, which accepts `int`,
`Fraction` and decimal *strings* (`as_exact("1.0080") == Fraction(126, 125)`).
Both frozen registers store every numeric value as an `"n/d"` rational string,
so no float appears even in serialisation —
`test_registers_contain_no_floats` walks the JSON to confirm it.

No CUDA path exists for exact rational arithmetic, and the full sweep runs in
well under a minute on one core, so this module uses no GPU. Reaching a GPU
kernel would require floats, destroying the property the step exists to
establish.

---

## Module map

| Module | Contents |
|---|---|
| `base.py` | `DataObject`, `Codec`, `StackParameters`, `derive_dynamic_parameters`, `as_exact` |
| `physics.py` | `Quantity`, `PhysicsCodec`, `basis_collision_report` |
| `elements.py` | `Element`, `Diatomic`, `ElementCodec`, `golay_address`, `periodic_separation_report` |
| `molecules.py` | `Molecule`, `MoleculeCodec`, `parse_formula`, `molecule_bundle`, `formula_from_bundle`, `composite_collisions`, `molecules_report` — the 51-species multi-carrier register |
| `harmonics.py` | `Interval`, `IntervalCodec`, `HARMONIC_LAYOUT`, `interval_register`, `interval_by_name`, `prime_exponents`, `product_complexity`, `euler_gradus`, `tet_step`, `tet_error`, `register_summary` — the 28-interval harmonic register, every coordinate derived from the ratio |
| `mathematics.py` | `RationalMatrix`, `Reflection`, `FieldElement` and their codecs |
| `lexicon.py` | `Vocabulary`, `Concept`, `LexiconCodec` (index-based, legacy; still tested, no longer loaded by the runtime) |
| `semantic_lexicon.py` | `SemanticConcept`, `SemanticLexiconCodec` — the 95 meaning-based concepts the `lexicon` register actually holds: 10 semantic primitives in 1/8 gradations, POS, arity, up to four (predicate, object) slots, a 20-bit checksum |
| `comparison_classes.py` | `ComparisonClass`, `ComparisonClassCodec`, `COMPARISON_LAYOUT`, `DegreeWord`, `MeasureScale`, `comparison_classes`, `class_by_name`, `classes_for_quantity`, `measure_scales`, `scale_for_quantity`, `degree_word`, `lexicon_agreement`, `register_summary` — the 45 comparison classes and the 11 scales, every dimension derived from the physics register |
| `_data/` | Frozen exact-rational snapshots; regenerate with `workflow/08a_ingest_registers.py` |

## Depends on

`glm_universal.substrate` (all four modules). Standard library only.

## Verify

```bash
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_data_objects.py -q      # 81 tests
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_semantic_lexicon.py -q  # 39 tests
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_molecules.py -q         # 39 tests
```

---

## v0.6.0 update: encoding lessons learned

The v0.5.0 → v0.5.2 work taught us several things about how to
encode data_objects correctly:

1. **Every data_object has 24 coordinates, no padding.**  The carrier
   shape is fixed by the Leech lattice, not by the data.  If a domain
   needs more than 24 coordinates, it must split across multiple
   carriers.

2. **Missingness is data, not an inconvenience.**  The element register
   uses a missingness mask (coord 17) so "0 because no measurement"
   is distinguishable from "0 as a value".  Any new domain with sparse
   data should follow this pattern.

3. **Aliases must avoid cross-domain collisions.**  The v0.5.2 fix
   (suppress short physics symbols that collide with element symbols)
   is a hard lesson: adding 60 physics concepts broke the chemistry
   analogy because `Li` resolved to `acoustic_intensity_level` instead
   of lithium.

4. **Primitive vectors must be unique.**  The v0.5.1 lexicon audit
   found 6 groups of concepts with identical primitive vectors.  The
   fix was to set every primitive on every concept (no defaults) and
   use 1/8 gradations where 1/4 was too coarse.

5. **Words are projections of meaning.**  The directive says "many
   words may be just projections of existing physics or math concepts".
   The semantic lexicon encodes words with 10 primitives, but `hot`
   is not yet encoded as "temperature at high scale" — it is a
   standalone concept.  Future work: encode words as projections.

6. **Register sizes (v0.6.0):**
   - physics: 726 quantities (EXT10 + SI7 + metadata)
   - chemistry: 118 elements (measured properties + Golay address)
   - mathematics: 22 objects (matrices, reflections, field elements)
   - lexicon: 95 semantic concepts (10 primitives + relations)
   - spatial: 28 MOG structures (trio, sextet, frame rows)

7. **A domain that does not fit one carrier gets two holdings, not a
   truncation.** The molecules register is the worked example of lesson 1:
   a molecule cannot be squeezed into 24 coordinates without loss, so the
   faithful bundle and the summary composite are both kept and the
   summary is *tested* for collisions instead of being trusted.
