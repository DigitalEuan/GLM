# `glm_universal/semantics` — meaning as the thing that gets encoded

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

```
semantics/
├── meaning.py     the meaning space: six kinds of determinate content, an
│                  injective 24-coordinate carrier, an exact round trip
├── reference.py   notation → meaning, or a refusal with a stated reason
├── relations.py   relations *derived* from meanings, each with a witness
├── graph.py       the grounded graph: nodes are meanings, notations hang off
│                  them, every edge is re-derived on demand
├── audit.py       what the inherited concept graph turns out to contain,
│                  measured rather than asserted
├── export.py      the graph and the purge plan written out as documents
└── __init__.py    public API exports
```

## The problem this package solves

The ARC-era concept graph in `arc_agi_17/results/glm_state.json` holds 4,282
concepts and 4,015 edges. Its carriers were produced by hashing a **spelling**
— `sha256(name)`, truncated to 24 bits, snapped to a Golay codeword — and its
edges were mostly produced by measuring distances between those carriers.

A hash of a spelling is a perfectly good identifier of a string, and it is not
a measurement of anything the string is about. Everything downstream inherits
that: geometry applied to a spelling answers questions about spelling.

Measured on the shipped state file (`report semantics` recomputes all of it):

| Measurement | Result |
|---|---|
| Concepts that denote anything determinate | **83 / 4,282** (1.9%) |
| Edges that state a re-derivable relation between two determinate referents | **2 / 4,015** |
| Edges that are carrier-proximity artefacts | 3,157 |
| Edges with at least one endpoint denoting nothing | 815 |
| Edges recording a pipeline event, not a relation | 39 |
| Mean legacy Hamming distance, semantically related pairs | 4547/376 ≈ 12.09 |
| Mean legacy Hamming distance, unrelated pairs | 12077/1009 ≈ 11.97 |
| Two random 24-bit words | 12 |
| Notations for one subject, mean legacy Hamming between them | 359/30 ≈ 11.97 |
| The same pairs in the meaning space | **0** |

The related and unrelated means straddle the random-word expectation of 12.
That is what "no signal" looks like when it is measured rather than assumed.

## What replaces it

A term is admitted only when the repository's registers pin down a
**determinate referent**, and then it is encoded *as that referent*. Six kinds
qualify:

| Kind | The determinate content | Notations that reach it |
|---|---|---|
| `number` | an exact rational | `2`, `two`, `XII`, `4/2`, `1+1`, `two*three` |
| `dimension` | an EXT10 exponent vector | `speed`, `velocity`, and the register's own symbols |
| `quantity` | a dimension with an exact coherent-SI magnitude | the seven SI defining constants |
| `element` | an atomic number | `hydrogen`, `H` |
| `compound` | a formula as sorted `(Z, count)` pairs | `water`, `H2O`, `dihydrogen monoxide` |
| `operation` | one of eight operations on meanings | `add`, `addition`, `plus`, `sum`, `+` |

Everything else is **refused, with a reason** — `beautiful`, `ago`, `abb`, and
the 4,198 dictionary words the ARC pipeline absorbed. A term with two
determinate readings (`II` is the Roman numeral two *and* two iodine atoms) is
also refused: 66 of the 1,768 named terms are ambiguous, and resolver order is
not allowed to decide them silently.

The carrier is 24 exact rationals:

```
0       kind        1..6
1..10   ext10       L M T I H N J A S B exponents
11      magnitude
12..21  formula     five (Z, count) slots
22      operation   0..8
23      checksum    sum (i+1) * c_i over coordinates 0..22
```

`encode` takes a `Meaning` and nothing else. There is no parameter through
which a spelling could reach the carrier, so "the carrier does not depend on
the notation" is enforced by the signature rather than asserted in prose.

Built over the register-backed vocabulary:

| | |
|---|---|
| Notations resolved | 1,705 |
| Meanings (nodes) | 357 — 156 dimension, 118 element, 39 number, 29 compound, 8 operation, 7 quantity |
| Binary edges | 6,210 |
| Ternary edges | 6,649 |
| Edges re-derived from the meanings they join | all of them |

## The relations

Fifteen binary and four ternary relations, each returning a `Claim` carrying
the arithmetic that makes it true, and each re-checkable from the meanings
alone by `verify`:

`same_meaning`, `same_dimension`, `si7_conflates`, `reciprocal_dimension`,
`magnitude_of`, `successor`, `divides`, `reciprocal`, `square`, `less_than`,
`contains_element`, `same_group_block`, `same_period`, `next_element`,
`atom_count`; and `product_of`, `quotient_of`, `sum_is`, `product_is`.

```
water / oxygen   : contains_element  -- Z1_2 Z8 contains 1 atom(s) of Z 8
energy / torque  : si7_conflates     -- EXT10 separates them (L^2 M T^-2 vs
                                        L^2 M T^-2 A^-1) and SI7 does not
hydrogen / helium: next_element      -- Z 2 = Z 1 + 1
two / four       : divides           -- 2 divides 4: 4 = 2 * 2
```

## Using it

```bash
PYTHONPATH=. python3 GLM.py -q "meaning of water"
PYTHONPATH=. python3 GLM.py -q "relate energy torque"
PYTHONPATH=. python3 GLM.py -q "report semantics"
PYTHONPATH=. python3 glm_universal/examples/semantic_replacement.py
```

```python
from glm_universal.semantics import build_graph, meaning_of, derive, verify

water, oxygen = meaning_of("water"), meaning_of("oxygen")
for claim in derive(water, oxygen):
    print(claim.relation, claim.witness, verify(claim))
```

`export.write_documents()` writes `semantic_graph.json` and
`semantic_purge_plan.json` beside the inherited state file. It reads
`glm_state.json` and never writes it: the purge is a document you can read,
not a deletion you cannot see.

## The formal counterpart

`RequestProject/GLM/Semantics/` proves in Lean 4 what this package relies on:

| Theorem | What it says |
|---|---|
| `decode_coords` | the round trip: a well-formed meaning is recovered from its carrier exactly |
| `coords_injective` | distinct meanings have distinct carriers, so carrier equality *is* meaning equality |
| `semantic_iff_respects` | a map on notations is information about the subject exactly when it factors through denotation |
| `spelling_not_semantic` | an encoding that separates every notation cannot be a function of meaning |
| `legacy_threshold_dichotomy` | on the measured Hamming distances, **no** proximity radius recovers synonymy: below 15 it splits synonyms, from 15 up it relates everything |
| `derived_relation_is_semantic` | a relation derived from meanings is a relation between meanings, by construction |
| `capacity_forces_refusal` | at the carrier's capacity, two distinct formulas collide — so refusal, not truncation, is the honest answer |
| `energy_torque_mem_boundary` | `(energy, torque)` lies in the EXT10 → SI7 boundary: distinct above, identical below |
