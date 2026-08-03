# Spatial arrangement, time, and pair-discovery round

## Question tested

This round asks a narrower, falsifiable version of whether a self-contained element Data Object can carry predictive chemical meaning:

1. What exactly changes when one message bit is toggled and the Golay word is recomputed (the proposed “blast radius”)?
2. Does a discrete sequence of Data Objects expose a useful bit-flip rhythm?
3. Do distances between pairs of Data Objects rank simple chemical similarity better than ordinary controls?
4. Can a MOG arrangement chosen on training elements retain its advantage on unseen elements?

This is a representation experiment, not a claim that the embedding is physical space or that it predicts reactions. The available 118-element table supports immediate tests of broad labels, but not stoichiometric compounds, bond energies, kinetics, phases, or reaction conditions.

## Reproduction

```bash
python3 spatial_chemistry_discovery.py
python3 -m unittest discover -s tests -v
lake build RequestProject.GolayMOG
```

The detailed deterministic output is in `results/spatial_discovery.json`; all fold-level pair results are in `results/spatial_pair_metrics.csv`.

## 1. A precise blast-radius test

“Blast radius” must specify both the state being toggled and the update rule. This round defines it as:

> toggle one of the 12 systematic message coordinates, recompute the extended binary Golay word, and count the changed coordinates in the resulting 24-bit word.

Because the encoder is linear, this response does not depend on the starting element. Under the fixed MOG convention, the source-row radius multisets are:

| MOG row containing source message coordinate | total changed-code-bit radii |
|---|---|
| 0 | 8, 8, 8, 12 |
| 1 | 8, 8, 8 |
| 2 | 8, 8, 8 |
| 3 | 8, 8 |

The JSON also records how every mask distributes its changes across all four destination rows.

This does **not** reproduce a `7–11 / 7 / 1 / 1` rule. There are two distinct operations that should not be mixed:

- toggling a stored codeword cell directly changes exactly one stored bit;
- toggling a message bit and re-encoding changes 8 or 12 codeword bits.

Thus the reported row rule may use a different MOG orientation, a nonlinear state transition, a neighbourhood propagation rule, or a different definition of “affects.” It is not rejected in every possible convention, but its precise operation is needed before the same quantity can be replicated.

## 2. Time as a discrete Data Object clock

No physical timescale is inferred. One **tick** is explicitly defined as moving from one subject to the next in a declared traversal. Assigning reflected Gray addresses by traversal rank gives exactly one message-bit flip per tick over all 117 transitions. Golay protection expands these to 59 bursts of size 8 and 58 bursts of size 12.

The flip count by Gray-message coordinate is:

```text
[58, 30, 15, 7, 4, 2, 1, 0, 0, 0, 0, 0]
```

This is a deterministic binary-clock pattern, not a discovered elemental frequency. Changing the subject ordering changes which elements meet at a tick, but not this rank-generated flip schedule. That distinction is important: any chemical signal comes from the traversal, while the Gray rhythm is supplied by the encoding.

Adjacency checks make this visible:

| Traversal | adjacent same-group fraction | adjacent same-period fraction |
|---|---:|---:|
| atomic number | 0.2222 | 0.9487 |
| period then group | 0.2222 | 0.9487 |
| group then period (positive control) | 0.8462 | 0.2222 |
| electron configuration, lexical | 0.1966 | 0.9487 |
| seeded random (negative control) | 0.0769 | 0.1368 |

The group traversal recovers groups because group is how that traversal was constructed; it is a positive control, not an independent chemical discovery. The next meaningful ordering test should derive a traversal from training-only physical observations and evaluate neighbourhood preservation on held-out elements.

## 3. Pair positioning and held-out similarity

For each representation, a pair score is the negative standardized Euclidean distance, so nearby objects predict the same broad label. Two endpoints were used:

- same PubChem `GroupBlock`;
- same recorded `StandardState`.

AUC is measured only on pairs of unseen test elements in five deterministic element folds. `0.5` is chance and `1.0` is perfect ranking. For the learned-layout condition, each fold searched the fixed MOG plus 128 seeded random coordinate permutations **using only training elements**, then evaluated the selected layout on test-test pairs.

Mean held-out AUC:

| Representation | same group/block | same standard state |
|---|---:|---:|
| atomic-number distance | 0.5685 | 0.6248 |
| Gray-message distance | 0.5847 | 0.5162 |
| Golay Hamming distance | **0.5943** | 0.5350 |
| Spatial Arithmetic polygon count/radius | 0.5637 | **0.6292** |
| fixed stacked-MOG geometry | 0.5389 | 0.4699 |
| training-selected MOG geometry | 0.5241 | 0.5114 |

The best same-group/block score in this limited comparison is Golay Hamming distance, but its margin over the atomic-number control is only about `0.026`. The Spatial Arithmetic radius representation is best for standard state by only about `0.004` over atomic number; both are monotone functions of atomic number here, so this is not evidence that polygon geometry adds information. No uncertainty interval or independent locked dataset supports treating these small differences as a stable effect.

Most importantly, searching 129 MOG arrangements on each training fold did **not** produce a reusable held-out geometry: selected-layout AUC was `0.5241` for group/block and `0.5114` for standard state. It did not beat the ordinary baselines and was close to chance.

## Findings

### Supported exact structure

- A traversal rank can be represented as a one-message-bit-per-tick Gray clock.
- The Golay layer turns those single-bit message transitions into exact 8- or 12-bit protected bursts.
- The re-encoding blast masks and their row distributions are completely reproducible.
- XOR is a symmetric pair contrast; Lean additionally verifies that identical inputs produce zero contrast and that either input is recoverable when the other is known.

### Not supported by this round

- The fixed MOG rows do not exhibit the stated `7–11 / 7 / 1 / 1` blast radii under the explicit linear re-encoding definition.
- Neither the fixed MOG geometry nor a training-selected coordinate permutation beats simple controls on the two held-out pair tasks.
- The Gray clock has no physical duration or elemental flip rate: it is an indexing clock until an independently measured temporal process is supplied.
- Pair proximity does not by itself represent a chemical interaction. Same-element XOR being zero means “no identity contrast,” not “no physical interaction.” Two hydrogen atoms, for example, require species, separation, electronic state, and an interaction endpoint before bond formation can be modelled.

## Best next experimental structure

The most defensible next object has three separate layers:

1. **subject/state object** — element or isotope, charge, electronic state, phase, identity code, and observations;
2. **spatial pose** — a declared coordinate frame, orientation, scale, and separation, rather than silently treating MOG cells as laboratory positions;
3. **interaction/event object** — ordered participants, stoichiometry, temperature, pressure, elapsed time or simulation step, and one measured endpoint.

The next round should use one genuine interaction dataset. A suitable first target is either gas-phase diatomic dissociation energy or phase-specific binary-compound formation enthalpy. The validation split must hold out complete elements or composition families. Compare ordinary chemical descriptors, atomic number, raw/Gray/Golay bits, fixed MOG, many random layouts, and training-only selected layouts. Only a repeated advantage on a locked test set should be called predictive ability.

For geometry subjects beyond elements, `spatial_arithmetic.py` can already encode and observe exact arithmetic expressions as geometric scenes. That is a verified codec: it demonstrates that a structured Data Object can carry mathematical meaning. It should remain conceptually separate from the empirical question of whether a particular geometry predicts chemistry.
