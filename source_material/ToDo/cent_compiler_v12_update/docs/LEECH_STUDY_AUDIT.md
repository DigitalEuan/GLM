# Separate-study audit: Leech-lattice move bigrams

This records an actual use of the compiler on an external study:
[`DigitalEuan/Leech-lattice`](https://github.com/DigitalEuan/Leech-lattice),
whose fourth report claims a **45.8% greedy top-1** score for predicting the
next Leech-lattice move under its leave-one-file-out protocol.

The uploaded repository contains the report, the study's flat Python modules
and its demo output, but not the packaged data (`data/codebook.json`,
`data/library_core.npz`, `data/exp_moves.json`) or the 442 Lean files. The report
names [`DigitalEuan/GLM`](https://github.com/DigitalEuan/GLM) as the corpus
source. That repository contains the matching **442 `.lean` files** under
`src/lean`.

## What was reconstructed

Using the study's own modules (inventory, deterministic 24-channel directions,
Leech addressing, and `MoveAlgebra`) over `src/lean`:

| Quantity | Result |
|---|---:|
| Lean files | 442 |
| Token parts | 1,487,625 |
| Inventory parts / Leech addresses | 39,992 |
| Address collisions | 0 |
| Distinct moves | 80,361 |
| Move occurrences | 1,487,183 |
| Adjacent transitions | 1,486,741 |

These are exactly the counts in the study's report and demo output. No Leech
generator, lattice vector or distance was invented by the compiler: the 24D
move vectors are the study's own address differences.

## Graph coverage: which parts the lattice graph actually omits

Rebuilding the study's own `LatticeGraph` over the same 442 files and 39,992
codebook addresses gives an exact split. The graph is not missing structural
tokens; it is deliberately scoped to them:

| Class | Addresses | Graph nodes | Result |
|---|---:|---:|---|
| Structural token parts | 20,458 | 20,458 | all covered |
| Bigrams | 10,421 | 0 | all 10,421 decompose to an existing token edge |
| Comments | 8,935 | 0 | non-structural |
| Frames | 63 | 0 | used only by the context layer |
| Tactics | 86 | 0 | used only by the context layer |
| Whitespace | 29 | 0 | non-structural |
| **Codebook total** | **39,992** | **20,458** | 19,534 addresses outside the graph's declared scope |

The graph itself has 20,458 nodes and 105,282 directed joinings, forming one
weakly connected component with zero isolated structural nodes. Every one of
the 10,421 bigram addresses maps to a directed token edge already present, so
inserting the bigrams as intermediate nodes adds 20,842 incidence edges but
**zero new token-to-token pairs**. The report's 568 frame-to-tactic joins are a
separate context graph; `lattice_graph.py` does not build them.

The graph is also sparse in file support, which is what makes a held-out part
look "missing": 14,388 of 20,458 parts (70.33%) and 78,079 of 105,282 joinings
(74.16%) occur in exactly one file. A node-only addition of all 19,534 omitted
addresses produces 39,992 nodes, 105,282 joinings, 19,534 isolated nodes and
19,535 components; it changes no structural reachability. Adding the bigrams as
bridges changes no token adjacency. Adding frame/tactic joins would add
context-level edges, not structural ones.

The genuine missing-parts measurement is therefore the study's leave-one-out
frontier, not the codebook set difference. Recomputing it on structural ticks
gives 70,038 / 828,762 = 8.4509% (median 7.59%), consistent with the report's
8.4% (median 7.1%). Those ticks are the authoring cost of a held-out file; they
are not recoverable from the graph in advance, and adding them makes coverage
100% by construction, not a new derivation or lattice relation.

Conclusion: the lattice graph does not identify missing structural parts
because none are missing in its scope. It identifies the classes it excludes by
design. Adding those classes as nodes has no measurable structural effect;
adding them as a context graph is a different experiment, not a repair of this
one.

## `cent` results

The reconstructed corpus was exported as a 19.9 MB
`cent-move-corpus/1` document and audited with the compiler:

```bash
python3 cent moves leech-move-corpus.json --holdout study
python3 cent moves leech-move-corpus.json --holdout strict
```

| Evaluation | Correct | Total | Result |
|---|---:|---:|---:|
| In-sample (no holdout) | 824,517 | 1,486,741 | 55.4580% |
| Study protocol (`--holdout study`) | 681,926 | 1,486,741 | **45.8672%** |
| Strict file holdout (`--holdout strict`) | 688,988 | 1,486,741 | 46.3422% |

The study protocol result rounds to the report's **45.8%**, so the compiler
independently reproduces the published figure from the study's corpus and
definition. The strict holdout differs because the study subtracts only the
held-out file's count of the evaluated pair, not every transition from that
file. The report itself discloses this distinction; `cent` keeps both modes
explicit rather than relabelling the study result as a clean holdout.

The in-sample number is not the claim and is shown only as the upper reference.
The `study` holdout has 73,645 transitions with no candidate; strict has
106,936. Net-displacement statistics use the exact integer 24D vectors.

## Follow-up: the explicit 24-bit class isomorphism

The study's class space also admits a clean group isomorphism
`Λ/2Λ ≅ F₂²⁴`: coordinates in the study's `leech_basis()` reduced mod 2.
On the actual 80,361 moves it produces exactly 63,257 distinct class words,
rank 24, and XOR composition. `cent leech-class` now re-derives those figures
from the declared basis and exported corpus: 80,361 moves, 63,257 class words,
rank 24, one zero-class move and 5,000/5,000 sampled XOR compositions. The
construction, checks and proposed minimal patch for `moves.py` are in
[LEECH_ISOMORPHISM.md](LEECH_ISOMORPHISM.md). This is a class index, not an
operation-matrix row or a Griess/Monster computation; the boundary and
admission sequence are recorded in
[OPERATION_MATRIX.md](OPERATION_MATRIX.md#leech-navigation-boundary).

## What the compiler did and did not do

It did:

- load and validate the declared corpus;
- count exact moves and transitions;
- compute exact bigram top-1 predictions with deterministic tie-breaking;
- apply the study's holdout subtraction precisely;
- compute exact displacement statistics from the 24D integer vectors;
- re-derive the 24-bit class words and sampled XOR composition through
  `cent leech-class`, using a caller-declared row-HNF basis.

It did not construct a Leech heat kernel, lattice metric/q-form, Griess algebra,
Monster action, Lean elaborator or Viazovska codebook. The study's own report
says the full Griess product is not implemented either. This audit is a
move-statistics and class-index use case, not a claim that the compiler now
implements those mathematical systems.

## Reproduction note

The full corpus is generated from the study's code and the GLM Lean tree; it is
not committed to this repository because it is a 19.9 MB derived artifact. The
local working paths used for this audit were:

- `../leech-lattice-study` — sibling study checkout, not part of this package;
- `../glm-study/src/lean` — sibling 442-file Lean source checkout;
- `../leech_bridge` — temporary package copy, reconstruction scripts and
  exported corpus, also outside this package.

The source modules are unmodified; the export joins their existing addresses
and move streams to the compiler's declared corpus format.

[`GLM_CENT_APPLICATION_AUDIT.md`](GLM_CENT_APPLICATION_AUDIT.md) records that a
Griess-product query currently overmatches generic cent multiplication. That
match is a finding, not an accepted Griess implementation.
