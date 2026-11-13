# Declared move-corpus audit

`cent_compiler/move_corpus.py` reads a declared move corpus and computes an
exact, descriptive baseline. It is deliberately separate from the Leech-lattice
heat-kernel proposal. The repository does not carry the Leech generators or the
80,361-move repertoire; `cent leech-class` audits a declared basis and corpus
when they are supplied, and was run against the external study export.

```bash
python3 cent moves path/to/move-corpus.json
python3 cent moves path/to/move-corpus.json --json
python3 cent moves path/to/move-corpus.json --holdout study

# Exact class-word audit: declared row-HNF basis + move corpus
python3 cent leech-class --basis path/to/basis.json --corpus path/to/move-corpus.json
python3 cent leech-class --basis path/to/basis.json --corpus path/to/move-corpus.json --json
```

## Exact class-word audit

`cent leech-class` solves each move vector in a declared row-HNF basis, reduces
the coordinates modulo 2 and composes the resulting class words by XOR. It
reports the basis determinant, moves decoded, distinct class words, F2 rank,
zero-class moves and a deterministic sample of composition pairs. The result
schema is `cent-leech-class/1`; the command refuses a non-lattice vector and
does not infer a lattice from the moves.

Run against the study's exported corpus and its 24x24 basis (determinant
`2^36`), the compiler re-derived:

| Check | Result |
|---|---:|
| Moves decoded | 80,361 |
| Distinct class words | 63,257 |
| Class space | 16,777,216 |
| F2 rank | 24 |
| Zero-class moves | 1 |
| Sampled XOR composition | 5,000 / 5,000 |

This is a class index, not a compute or carry route. It does not transplant the
lattice metric or quadratic form, and it does not implement a Griess product,
Monster action, Lean certificate or codebook optimizer. Those remain separate
D10 layers.

## GLM alignment

The audit is deliberately adapter-shaped for the GLM system: standard-library
Python only, exact integer arithmetic, no float or NumPy path, JSON input and a
JSON schema with an output certificate. It can be invoked as a subprocess or
imported as `cent_compiler.leech_class` without importing `glm_universal`; the
basis and move provenance stay explicit in the report. This is the first
compiler-side seam for the GLM substrate, not a claim that the full Leech or
Monster layer is present.

## Schema

```json
{
  "schema": "cent-move-corpus/1",
  "provenance": "where these sequences came from",
  "moves": {
    "m1": {"vector": [1, 0], "weight": "1"},
    "m2": {"vector": [0, 1], "weight": "1"}
  },
  "sequences": [
    ["m1", "m2", "m1"],
    ["m2"]
  ]
}
```

- `sequences` is required: a non-empty list of non-empty move-id lists.
- `moves` is optional when only bigrams are needed; move ids used by sequences
  are then inferred.
- `vector` is optional per move. If every used move has an integer vector, the
  audit reports net displacement; otherwise that section is a gap. Vectors need
  not be 24-dimensional.
- `weight` is optional and defaults to `1`; it must be a positive exact
  rational. The bigram baseline counts observed transitions, so it does not
  apply weights. Weights are validated for the corpus contract but are not used
  to invent a heat kernel.

## What is computed

- sequence, move-occurrence and adjacent-transition counts;
- unique used moves and vector dimension;
- the most frequent next move for each current move, with ties broken by the
  lexicographically smallest move id;
- in-sample top-1 accuracy over every adjacent transition;
- if vectors exist: each sequence's net integer displacement, squared norm,
  median and mean net squared norm, and mean squared move norm.

The result schema is `cent-move-corpus-report/1`. The default report states
that the `top1` evaluation is **in-sample** and has **no held-out split**. The
optional `--holdout` modes add a separate `holdout` section:

- `--holdout study` follows the published study protocol: for each evaluated
  transition, subtract only the held-out file's count of that actual pair.
  This reproduces the separate Leech study's reported 45.8% on its 442-file
  corpus. It is **not** a strict file holdout.
- `--holdout strict` removes every transition of the held-out file from the
  prediction counts. On the same corpus this gives 46.3422%, not 45.8%.

See [LEECH_STUDY_AUDIT.md](LEECH_STUDY_AUDIT.md) for the reconstructed corpus,
exact counts and provenance.

## Current limits

- This does not compute the discrete Green's function or heat kernel
  \(K(A_0,A_t,t)\).
- It does not construct the Leech lattice, its 24D translation group, the 80,361
  observed moves or the theta series. `cent leech-class` audits a caller-declared
  basis and move set; it does not infer either.
- The class-word audit does not transplant the lattice metric or quadratic form;
  the 24-bit map is a group isomorphism, not an isometry.
- It does not implement a Griess algebra product, Parker-loop cocycle or Monster
  action.
- It does not invoke Lean, elaborate dependent types or issue proof
  certificates.
- It does not solve Viazovska-style packing or codebook optimization.

Those are tracked as open D10 items in
[`PHYSICAL_COMPILER_ROADMAP.md`](../PHYSICAL_COMPILER_ROADMAP.md) (completed ledger). The audit is the
first honest prerequisite: it can validate the corpus and the bigram baseline
before any lattice dynamics claim is made.

## Tests

```bash
python3 tests/test_moves.py  # 11/11 focused checks
python3 tests/run_all.py     # canonical gate
```
