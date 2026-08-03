# Dimension Projection: audit and corrected study

## Executive finding

The useful mathematical object in the study is the **coordinate projection
(puncturing)** of the extended binary Golay code:

\[
\pi_S:C\subseteq\mathbf F_2^{24}\longrightarrow\mathbf F_2^{|S|},\qquad
(\pi_S(x))_j=x_{S_j}.
\]

This map is linear and can be studied exactly. The new
`dimension_projection.py` does that without Monte Carlo error.

The previously reported sharp change after 12 coordinates is real as a change
in the chosen **AND-closure statistic**, but its earlier physical explanation
is not justified. For the prefix projections used in the study:

| kept coordinates | rank | distinct image words | fibre size | surjective? | minimum image weight | exact AND closure |
|---:|---:|---:|---:|:---:|---:|---:|
| 4 | 4 | 16 | 256 | yes | 1 | 1.000000000 |
| 6 | 6 | 64 | 64 | yes | 1 | 1.000000000 |
| 8 | 8 | 256 | 16 | yes | 1 | 1.000000000 |
| 10 | 10 | 1024 | 4 | yes | 1 | 1.000000000 |
| 12 | 12 | 4096 | 1 | yes | 1 | 1.000000000 |
| 14 | 12 | 4096 | 1 | no | 2 | 0.258056641 |
| 16 | 12 | 4096 | 1 | no | 2 | 0.075317383 |
| 18 | 12 | 4096 | 1 | no | 3 | 0.026885986 |
| 20 | 12 | 4096 | 1 | no | 4 | 0.012603760 |
| 22 | 12 | 4096 | 1 | no | 6 | 0.007774353 |
| 24 | 12 | 4096 | 1 | no | 8 | 0.006893158 |

These values count all ordered pairs, including equal pairs, and are therefore
exact for the image sets and stated counting convention.

## Why the apparent 12-to-14 transition occurs

The Golay code has dimension 12. In the selected prefix ladder, every
projection through 12 coordinates has full rank equal to the number of kept
coordinates. Consequently its image is the *entire* cube
\(\mathbf F_2^n\). The entire cube is automatically closed under bitwise AND,
so closure 1.0 at 4–12 dimensions does not reveal a dynamical phase.

At 12 coordinates the map is a bijection between the 4096 codewords and all
4096 12-bit strings. Keeping 14 coordinates still gives 4096 image words, but
now they occupy only one quarter of the 14-cube. AND need not remain in that
proper linear subspace, so the closure statistic falls. This is an algebraic
change from a surjective projection to an injective embedding, not evidence by
itself of a physical phase transition.

The coordinate choice also matters. A deterministic sample of 20 subsets found:

| dimension | sampled ranks | sampled exact AND-closure range |
|---:|:---:|:---:|
| 8 | {8} | 1.0000–1.0000 |
| 10 | {9,10} | 0.5078–1.0000 |
| 12 | {11,12} | 0.5078–1.0000 |
| 14 | {12} | 0.2581–0.2617 |
| 16 | {12} | 0.0753–0.0771 |

This sensitivity check is exact for each sampled subset, but it is not an
exhaustive distribution over all subsets. It shows why “dimension” must never
be reported without also specifying the projection map or coordinate set.

## What is validated

The following are finite algebraic facts of the implemented Golay code:

- There are 4096 codewords and the full code has rank 12.
- The full weight distribution is
  \(1+759z^8+2576z^{12}+759z^{16}+z^{24}\).
- The full minimum nonzero Hamming weight is 8.
- Coordinate projection commutes with XOR and cannot increase Hamming weight.
- Every fibre of a linear coordinate projection has equal size.
- The exact prefix-projection table above is reproducible.
- All codewords are pairwise orthogonal in the supplied representation; with
  dimension 12 in length 24, this establishes self-duality.

## Claims that need correction

### 1. “The Hodge Conjecture fails at 24D”

This is unsupported and should be removed. A binary code and its AND operation
have not been shown equivalent to a smooth projective complex variety, Hodge
classes, algebraic cycles, or cup product. A failed code predicate cannot be a
counterexample to the Hodge conjecture.

### 2. “Data is physics / structural identity”

The software defines analogies—calling Hamming weight “mass,” syndrome weight
“energy,” and a chosen inverse-square score “gravity.” Definitions make those
quantities valid model outputs, but do not establish identity with physical
mass, energy, or gravity. Independent empirical predictions would be needed.

### 3. “Every vector can descend / reaches ground in about four steps”

The supplied results are sampled. The greedy procedure can also stop whenever
no one-bit move lowers syndrome weight; the script does not prove global
convergence. “About four” depends on the sample, random seed, syndrome basis,
and algorithm. It is not an invariant of dimension projection.

### 4. Nearest-codeword and attraction measurements

`ldp_internal.py` examines only 500 of 4096 codewords for “nearby” and nearest
codewords; `compute_attraction_field` examines only 200. It then labels the
sampled nearest point as the nearest codeword. Those fields can therefore be
wrong. The 24-bit extended Golay decoder should be used for exact nearest
recovery within its correction radius, or all 4096 codewords should be checked.
The inverse-square force is an imposed scoring rule, not an observed force.

### 5. Symmetry-breaking test

The old chi-square comparison used a uniform expectation of 1/8 for each
“quadrant.” But an 8-bit block is labelled high when its weight is at least 4,
which occurs with probability 163/256, not 1/2. Thus even uniformly random
24-bit vectors have nonuniform H/L labels. This is visible in the old output:
its random control had chi-square 2498.9 against the incorrect uniform null.
Using the correct independent-binomial null gives chi-square about 133.74 for
the codeword table. That can support a statement that this particular fixed
3×8 partition has a distribution differing from the ambient cube; it does not
show spontaneous physical symmetry breaking.

### 6. “Topological invariants”

Hamming weight distribution, minimum distance, and self-duality are coding or
metric invariants. Calling arbitrary bit flips “continuous deformation” does
not make the sampled perturbation test topological. Also, testing only 100
sampled codewords pairwise does not prove self-duality, although exhaustive
checking does succeed here.

### 7. Conservation and collision language

Parity under XOR is a universal bit identity, not special evidence for the
Golay model. The stated mass-defect formula
\(\operatorname{wt}(a)+\operatorname{wt}(b)-\operatorname{wt}(a\land b)\)
is always nonnegative for any bit vectors. Its lower bound depends on which
pairs are admitted: zero with an octad gives 8, so the document’s blanket
“mass defect ≥ 12” is false if all codeword pairs are included. The sampled
script happened to report 12 because of its selected pairs.

### 8. Reproducibility and runnable state

`ldp_investigation.py` and `ldp_internal.py` import `ldp_nrci`, which is absent
from this checkout. They currently fail before running. Their saved JSON files
are historical outputs, not regenerated verification. The scripts also use an
unseeded global random generator and several changing random subsamples.

### 9. Other concrete defects

- The old forbidden-gap calculation includes the zero codeword when finding the
  minimum codeword weight, yielding the nonsensical range `1..-1` and size -1.
  Excluding zero gives the low-weight gap 1–7.
- “Syndrome is the local energy gradient” is inaccurate. A syndrome is a linear
  diagnostic vector; syndrome *weight* is the chosen scalar score. A discrete
  steepest-descent direction must be computed from neighbouring score values.
- Block sums are a many-to-one summary of a 24-bit word, not spatial coordinates
  unless the model explicitly defines them as such.
- The old 4D/8D/12D labels describe punctured images of one 24-bit code. They are
  not the named independent `[4,2,2]`, `[8,4,4]`, and `[12,6,6]` codes claimed
  in the document: the measured prefix images have ranks 4, 8, and 12.

## Recommended interpretation

A defensible study is:

> “How do rank, fibre multiplicity, minimum projected weight, weight
> distribution, and Boolean-operation closure vary when the extended binary
> Golay code is punctured onto specified coordinate subsets?”

That question is precise, reproducible, and fully finite. Use “dimension” for
ambient coordinate count, “rank” for the image’s algebraic dimension, and
always publish the coordinate subset. Treat physical and Hodge terminology as
optional analogy, never as a validated conclusion.

## Running the corrected audit

```bash
python dimension_projection.py --self-test
python dimension_projection.py --json dimension_projection_results.json
```

The JSON contains enough counts to recompute every displayed closure rate.
`coordinate_subset_sensitivity(dimension, samples, seed)` performs a documented,
deterministic coordinate-choice sensitivity study.
