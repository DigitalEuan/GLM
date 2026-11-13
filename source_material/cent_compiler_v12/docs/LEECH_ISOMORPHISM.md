# The 24-bit class isomorphism

> **Provenance:** this construction was worked out by the assistant in
> analysis. `cent leech-class` now re-derives the class words from a declared
> row-HNF basis and the exported move corpus; the basis and moves remain
> caller-declared evidence. The isomorphism is still not a compute route, a
> lattice metric, a Griess product or a Monster action.

The study's move algebra lives in `Λ/2Λ`, a group of order `2^24`. Its
`class_key()` is a canonical residue modulo `2Λ` in the ambient `Z^24`; those
residues are **not** 24-bit coordinates (their pivot range is 16 down to 2).
There is, however, a clean group isomorphism hiding just beside it.

## Construction

Let `B` be the study's row-HNF `Z`-basis of the Leech lattice
(`leech_basis()`, determinant `2^36`). Every lattice vector `x` has a unique
coordinate vector `c ∈ Z^24` with

```
x = c B.
```

Define

```
φ(x) = (c_0 mod 2, ..., c_23 mod 2) ∈ F₂^24.
```

Because `B` is a basis, `φ(x) = 0` exactly when `x ∈ 2Λ`. Therefore `φ`
factors through `Λ/2Λ` and is a bijection

```
φ : Λ/2Λ  ≅  F₂^24.
```

It is a **group isomorphism**, and composition is coordinate-wise XOR:

```
φ(x + y) = φ(x) ⊕ φ(y).
```

This is the F₂ basis the study's `moves.py` docstring already points at when it
says composition is "coordinate-wise XOR under any F2 basis of the quotient";
the module did not construct that basis or expose the bit key.

## Checked on the real corpus

The construction was run on all 80,361 distinct moves reconstructed from the
442-file GLM corpus. `cent leech-class` now re-runs this check from the declared
basis and exported corpus. Every move solved exactly in `B` (no division
remainder), so all are genuine lattice vectors.

| Check | Result |
|---|---:|
| Moves decoded | 80,361 |
| Distinct 24-bit class words | **63,257** |
| Study's reported occupied classes | 63,257 |
| F₂ rank of the observed class words | **24** |
| Zero-class moves | 1 |
| Random pairs with `φ(x+y)=φ(x)⊕φ(y)` | 5,000 / 5,000 |
| Study `class_key` → bit-word map on observed classes | bijective |
| Compiler-side `cent leech-class` | same counts; 5,000/5,000 sampled XOR pairs |

The rank being 24 matters: the observed repertoire's class words span the
entire `F₂^24`, so there is no smaller linear class invariant to exploit. The
63,257 observed classes are a subset of the 16,777,216 possible ones, but their
span is the whole index space.

As a representation cross-check, the class bigram scored
`575,538 / 1,486,741 = 38.7114%` under the study protocol, close to the
report's 38.8% figure. That is evidence the bit words carry the same class
information, not a claim of exact reproduction of that separate model.

## What this proposes for the study

Keep `class_key()` for the existing type lookup and as a readable canonical
representative. Add a compact **bit key** for class algebra:

```python
# leechlean/cosets.py, proposed
def basis_coords(x):
    c = [0] * 24
    for i in range(23, -1, -1):
        s = int(x[i]) - sum(c[j] * int(leech_basis()[j, i])
                           for j in range(i + 1, 24))
        p = int(leech_basis()[i, i])
        if s % p:
            raise ValueError("not in the Leech lattice")
        c[i] = s // p
    return c

def class_bits(x):
    c = basis_coords(x)
    return sum((c[i] & 1) << i for i in range(24))
```

Then in `MoveAlgebra`:

- store `self.bits_by_move[key] = class_bits(key)`;
- use an `int` key for class-level tables (24 bits, not a 24-tuple);
- add `class_convolution_bits(a, b) -> a ^ b`;
- keep the existing tuple `class_convolution()` for compatibility and for
  operations that still need the canonical representative.

This is a practical assist for the class-level work: composition of class
words becomes XOR instead of another `class_key()` reduction, the key is a
single integer, and class-first candidate tables can be indexed directly by the
24-bit word. It does not change the move or part predictions; it makes the
index-space representation explicit and cheap.

## What it is not

This is a **group isomorphism**, not an isometry of quadratic spaces. The
`q`-form and type map are not transplanted by this note. The study's
`class_pairing()` should continue to use its representatives unless a separate
Gram-matrix formula is derived and checked. The note also does not claim a
Griess product, a Monster action, or a Lean formalization.

## Compiler implementation

```bash
python3 cent leech-class --basis path/to/basis.json --corpus path/to/move-corpus.json
```

The command accepts a JSON list of row-HNF basis rows and a
`cent-move-corpus/1` document. It solves exact coordinates, emits one integer
class word per move, checks XOR composition on a deterministic sample and
reports the F2 rank. It uses only the standard library and exact integer
arithmetic, so it is suitable for the GLM's exact substrate and can be called
as a subprocess without importing `glm_universal`.

## Compiler boundary

This is a class index, not a compiler operation method. It is not a
`cent matrix` row: it does not compute an operation, carry a signal, or supply
a lattice metric, Griess product or Monster action. The compiler-side audit is
now present, but the class map remains outside the operation rows. See the
[Leech navigation boundary](OPERATION_MATRIX.md#leech-navigation-boundary) for
the admission sequence and the separate Griess/Monster gaps.

## Provenance

- Study: `DigitalEuan/Leech-lattice`, fourth report.
- Corpus: `DigitalEuan/GLM`, `src/lean`, 442 files.
- Basis: the study's `leech_basis()` (row-HNF, determinant `2^36`).
- Moves: the study's own addresses and `MoveAlgebra` streams.
- The exact reconstruction and exported corpus are described in
  [LEECH_STUDY_AUDIT.md](LEECH_STUDY_AUDIT.md).
- Compiler audit: `cent_compiler/leech_class.py`, run on the exported corpus;
  the basis and moves are supplied by the caller and are not embedded here.
