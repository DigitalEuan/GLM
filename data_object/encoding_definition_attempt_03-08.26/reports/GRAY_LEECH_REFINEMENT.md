# Gray / Golay / MOG / Leech refinement — testing round 2

## What changed

This round implements all three requested refinements:

1. element identity input is now a 12-bit reflected Gray code of atomic number;
2. every MOG cell has a fixed, distinct 24-dimensional Leech-lattice minimal-vector address, while measured dimensions are attached to those cells as typed channels;
3. the generated object table contains all 118 elements.

The complete machine-readable output is `data/objects/elements.jsonl`; its schema and the full address table are in `schemas/element_data_object_v2.json`.

## Identity pipeline

For atomic number `Z`, the v2 object computes

```text
Gray(Z) = Z XOR floor(Z/2)
          ↓ 12 least-significant-first message bits
systematic extended binary Golay [24,12,8]
          ↓ fixed MOG permutation
4 × 6 MOG occupancy
```

The legacy binary encoding remains in the experiment only as a named control. The regenerated benchmark compares six Gray configurations with the existing controls.

### Exact locality result—and an important boundary

For all 117 consecutive pairs from element 1 through element 118, the **Gray messages differ in exactly one bit**. The mean message Hamming distance falls from `1.9658` for ordinary binary to exactly `1.0` for Gray.

After Golay encoding, consecutive Gray identities differ by 8 or 12 bits (mean `9.9829`), rather than one. This is expected: a `[24,12,8]` error-correcting code deliberately separates every distinct pair by at least eight bits. Therefore Gray locality and Golay error separation cannot both hold in the same Hamming metric at the same layer. The coherent design keeps both layers:

- use the 12-bit Gray message for subject-neighbourhood calculations;
- use the 24-bit Golay word for integrity, MOG placement, and geometry;
- never claim one-bit adjacency of the Golay codewords.

Atomic-number adjacency is only one declared relation. Chemical similarity is not always atomic-number adjacency, so later rounds should test alternative Gray orderings (periodic-table traversal, group/block traversal, and learned orderings fitted only on training data) rather than assuming that consecutive Z always means related.

## 24-dimensional addresses and semantic dimensions

Each of the 24 MOG cells receives a distinct vector from the minimal-vector family of the Leech lattice. In the integer-coordinate model these have shape `(±4, ±4, 0^22)` and squared norm 32; after dividing coordinates by `sqrt(8)`, squared norm is 4. The selected set contains 24 distinct addresses and its address matrix has full rank 24.

This gives every cell:

- a stable cell identity;
- an exact 24D geometric address;
- distances and inner products to every other cell;
- a stable slot to which a semantic measurement dimension can be assigned.

The first schema maps all 16 non-identity source dimensions to cells: atomic mass, electron configuration, electronegativity, atomic radius, ionization energy, electron affinity, oxidation states, standard state, melting point, boiling point, density, group/block, discovery year, period, group, and CPK display colour. Eight addresses remain reserved.

The crucial distinction is between an **address** and a **value**. A 24-bit identity word has only 16,777,216 possible states and cannot losslessly contain an unbounded collection of real measurements, text, units, uncertainty, conditions, and provenance. Packing values into those bits would either lose information or make identity change whenever a measurement is revised. Instead, v2 makes the full Data Object self-contained as a structured record:

```text
Data Object = identity + protected codeword + MOG view
            + typed measured channels + provenance
```

Each channel lives at a Leech-addressed cell but retains its full value, unit, explicit missingness, and source linkage. This is a genuine encoding of all currently available meaning *within the Data Object*, without confusing a finite identity code with the entire payload. Future measurements can add uncertainty, method, temperature, pressure, phase, isotope/ion state, and citations without breaking identity.

The assigned Leech geometry is a coherent mathematical coordinate system, not yet evidence of a chemical law. Predictive value must be tested against random address assignments and ordinary tabular baselines.

## Full periodic table output

`data/objects/elements.jsonl` has exactly 118 records in atomic-number order. Every record includes:

- atomic number, symbol, and name;
- Gray integer and 12 message bits;
- 24-bit Golay codeword and 4×6 MOG ordering;
- all 16 mapped dimensions, including explicit `null` plus `missing: true` where the source has no value;
- units where applicable;
- MOG-cell and Leech-address references;
- source-record linkage.

This is full **element coverage**, not complete chemical knowledge: the source has missing or aggregate fields, and it does not describe every isotope, ion, allotrope, phase, excited state, compound, or reaction condition.

## Second-round predictive result

The same seven atomic endpoints and held-out protocol were rerun with Gray message bits, Gray Golay bits, and Gray MOG planar/stacked/cylindrical/spherical configurations. Lower normalized MAE is better:

| Configuration | normalized held-out MAE |
|---|---:|
| cubic atomic-number baseline | 1.0000 |
| legacy binary message | 1.0254 |
| legacy binary Golay word | 1.1001 |
| best random layout | 1.1152 |
| **Gray message** | **1.1516** |
| fixed binary MOG planar | 1.1682 |
| **Gray MOG planar** | **1.1898** |
| **Gray MOG cylinder** | **1.2112** |
| **Gray MOG stacked** | **1.2126** |
| **Gray Golay word** | **1.2141** |
| **Gray MOG sphere** | **1.2250** |

Gray coding exactly achieves the requested local input ordering, but it does **not** improve prediction in this small atomic-property test. The cubic-Z baseline remains best. This is useful separation of two claims: locality is proved; predictive chemistry remains empirical and is not supported by this round.

## Verification

The audit in `results/gray_leech_audit.json` confirms:

- 118/118 Gray round trips;
- 118 distinct Gray messages and Golay words;
- one-bit Gray-message adjacency for all consecutive elements;
- 24 distinct norm-4 Leech addresses;
- full rank of the 24-address matrix;
- valid fixed MOG permutation.

The Lean development proves, without `sorry`:

- Gray identity decode/encode round trip on all admitted elements;
- injectivity of their Gray addresses;
- one-bit adjacency for consecutive admitted atomic numbers;
- MOG-coordinate bijectivity;
- norm and injectivity of all fixed Leech addresses;
- symmetric XOR interaction.

## Recommended next test

1. Add observation-level metadata to every numerical channel: uncertainty, method, phase, temperature, pressure, and citation.
2. Predeclare three subject orderings: atomic number, periodic group/block traversal, and electron-configuration traversal. Gray-code each ordering and test held-out chemical-family neighbourhood preservation.
3. Compare the fixed Leech address map with many seeded random maps. Use only rotation/permutation-invariant 24D descriptors unless orientation has a predeclared meaning.
4. Separate immutable subject identity from state identity: element, isotope, charge, electronic state, and phase need explicit fields.
5. For interactions, move to complete species with stoichiometry and conditions. Begin with one clean endpoint such as diatomic dissociation energy or phase-specific binary formation enthalpy.
6. Freeze an external test set before selecting semantic-to-address mappings. A mapping should be retained only if it beats tabular and random-address controls on unseen elements or composition families.

## Reproduction

```bash
python3 gray_leech_data_objects.py
python3 golay_mog_experiments.py --run
python3 -m unittest discover -s tests -v
lake build RequestProject.GolayMOG
```
