# Status

*The one document to read first. What is done, what is open, and how to check
any of it without recomputing anything by hand.*

Last reconciled against a full re-run on 2026-08-25.

Every count below is produced by `overlay/glm_universal/figures.py` and written
to [`overlay/FIGURES.md`](overlay/FIGURES.md);
`overlay/glm_universal/tests/test_figures.py` fails if this document and the
code disagree. If a number here looks wrong, regenerate rather than edit:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.figures --write
```

---

## 1. Where the work stands, in one table

| instrument | command | result |
|---|---|---|
| test suite | `python3 -m pytest glm_universal/tests -q` | 1,677 tests across 37 test files, 8,851 subtests, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **83 / 83** — 73 answered, 10 refused as expected, 0 unexpected refusals, 0 confidently wrong, 0 errored |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites, every suite above its baseline |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 errored, 0 surprises |
| Lean development | `lake build` (repository root) | 27 Lean files, 6,390 lines, **0 `sorry`** |
| figures | `python3 -m glm_universal.figures --write` | regenerates `overlay/FIGURES.md`; every documented count |

The package is `glm_universal` **v1.3.0**: nine sub-packages, 61 modules,
**6 registers** holding 1,040 carriers (physics 726, chemistry 118, molecules
51, mathematics 22, lexicon 95, spatial 28), **18 query kinds** one of which
dispatches **25 report subjects**, and 3 tasks.

---

## 2. What is done

Each entry names the thing that recomputes it, so nothing here has to be taken
on trust. `MASTER_PLAN.md` carries the same list phase by phase with more
detail.

**Substrate and algebra.** Complete syndrome decoding with no silent tie-break;
the full Leech lattice in place of Construction A (kissing number 196,560); the
exact 2A Sakuma product in place of the XOR shortcut; the six-facet orthogonal
decomposition with the lattice index that says what a facet reading loses; the
`LEGACY_TO_CORE` frame bridge, verified an isometry.

**Registers.** Six of them. Physics (726 quantities, EXT10 exponents and unit
strings cross-checked against each other), chemistry (118 elements),
**molecules** (51 species and ions, every coordinate derived from the element
register at load time, bundle and composite collisions tested at 0),
mathematics, lexicon (95 concepts, 380 explicit relation triples) and spatial.

**Reasoning.** 27 modules. Analogy by named relation, dimensional verification,
Buckingham-Pi from an exact rational nullspace, the Walsh–Hadamard transform
decoder, the deep-hole walk, term arithmetic, unit parsing with the steradian
priced rather than silently redefined, and element-coverage widening that
labels every widened cell by provenance.

**Values.** Reals held as processes with no float anywhere; written arithmetic
over them including `exp`, `log`, `sin`, `cos`, `tan` and real powers; decided
inequality and refused equality; the delta–sigma modulator with its proved
`1/N` rate and, in 24 coordinates, the separating functional that proves a
target outside the hull unreachable.

**Meaning.** The grounded graph — 357 meanings, 1,705 notations, 12,859 edges,
every one re-derived on demand. The inherited ARC-era concept graph was
audited and the decision recorded: **demoted to evidence**, and
`tests/test_inherited_graph.py` enforces it by walking the imports of every
module that answers a question.

**Analogy.** The layer that closed the previous round's five wrong answers, and
the three lexicon/benchmark corrections that closed the last three misses.
Write-up: [`ANALOGY_LAYER_STUDY.md`](ANALOGY_LAYER_STUDY.md).

**Measurement.** Three instruments that do not trust each other: probes
(library boundaries), benchmarks (solver functions) and the end-to-end
evaluation (the CLI in a fresh interpreter per question, scored asymmetrically
so a confident wrong answer is worse than a refusal). Write-up:
[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md).

**Documentation binding.** `figures.py` recomputes every documented count and
`tests/test_figures.py` makes a stale figure a test failure.

**The Lean development.** 27 files, no `sorry`. Layer theory and the four
concrete boundaries; the Golay code, its sextet geometry, its coset census and
its dynamics; Cesàro convergence of the perturbation chain's time averages with
the explicit rate `|cesaro μ N f − 1/4096| ≤ 24/N`; the meaning carrier; the
value-layer error budgets; and the state–field map `Y(u, z)` at the Griess
layer of the 2A algebra, with the exact obstruction that shows the finite layer
is not a vertex algebra.

---

## 3. What is open

This is the whole list. Nothing else in the repository is claimed as pending.

### 3.1 The one gap the evaluation still finds

**Ranking an unregistered formula.** `nearest to PbCl2` refuses. The formula
parser reads `PbCl2` and the molecule codec would encode it — every coordinate
is derived from the element register, so no new datum is needed — but `nearest`
resolves its operand against the names a register *enumerates*. Joining the two
is the work item; it is the evaluation set's single `gap` case,
`nearest-unregistered-molecule`.

### 3.2 Named as untouched

The list is kept in `MASTER_PLAN.md` §7.9; this is the same list.

* **The infinite-dimensional half of the VOA bridge.** `VOA.lean` builds the
  state–field map `Y(u, z) = Σ uₙ z⁻ⁿ⁻¹` at the Griess layer of the
  3-dimensional `2A` algebra and proves what that layer carries — truncation,
  skew-symmetry, an invariant form that invariance itself forces,
  self-adjoint modes, nondegeneracy, and the vacuum `(4/5)(e₀+e₁+e₂)`. It also
  proves why that is as far as a finite model reaches:
  `borcherds_commutator_fails` shows the commutator formula at `m = n = 1`
  fails on the axis triple, so the modes the truncation discards are
  load-bearing. Building them means leaving the finite-dimensional setting,
  and that is not done.
* **Multi-domain analogy.** `heat : temperature :: force : ?` is refused with a
  stated reason rather than answered wrongly, which is correct but not an
  answer. Answering it needs a way to pose a question whose four operands do
  not live in one register.
* **The `O(1)` LLVQ table.**
* **The Niemeier deep-hole census** — the generalisation of `Golay/Census.lean`
  over the 23 Niemeier lattices, and with it the claim that a *trajectory
  distribution* classifies them.
* **Open vocabulary.** The vocabulary is exactly the registers; there is no
  coordinate for *justice*, and the semantics layer refuses rather than
  inventing one. This is a commitment, not an oversight.
* **Words as projections.** `hot` is a standalone concept, not "temperature at
  high scale".
* **The delta–sigma / quantiser-with-feedback directions** — cascaded loops,
  error feedback through a symmetry-commuting rational matrix, subtractive
  dither with an equidistributed sequence, sigma–delta on the shells, and the
  Gibbs-style rule. Explicitly **exploratory and not started**; they sit behind
  everything above.

### 3.3 Ongoing rather than finishable

* **`related_to` as a residue.** 66 of the lexicon's 380 triples are
  `related_to`, which records that a link exists without saying which. The
  analogy layer deliberately refuses to transport it, so each one is an
  analogy the machine must decline. Converting them to the relations they
  actually are is open-ended.
* **Sparse chemistry.** 1,257 of 1,652 element cells are filled. The coverage
  module measures the sparsity and widens it by derivation, one linear fit and
  cross-checking, and writes nothing back into the register — deliberately, so
  that an estimate is never mistaken for a measurement.

---

## 4. Re-verifying the whole thing

In order, from the repository root. The last step is the one that catches a
document drifting from the code.

```bash
lake build                                                   # 27 files, no sorry
rg -n 'sorry|admit' RequestProject/GLM                       # expect nothing

cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests -q        # the whole suite
PYTHONPATH=. python3 -m glm_universal.capabilities           # 33 probes
PYTHONPATH=. python3 -m glm_universal.benchmarks             # 5 suites
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8    # 83 CLI cases
PYTHONPATH=. python3 -m glm_universal.figures --write        # regenerate FIGURES.md
```

Spot checks that exercise the runtime the way a user does:

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report analogies"        --verify-tct
PYTHONPATH=. python3 GLM.py -q "report molecules"        --verify-tct
PYTHONPATH=. python3 GLM.py -q "report chemistry coverage" --verify-tct
PYTHONPATH=. python3 GLM.py -q "report semantics"        --verify-tct
```

Each returns `VERIFIED True`: the Three Column Thinking template regenerates
the answer's figures in a fresh interpreter and compares them with what was
printed.

---

## 5. The document map

| document | what it is for |
|---|---|
| `README.md` | the repository's front door |
| `STATUS.md` | this file — the current state and the to-do list |
| `MASTER_PLAN.md` | the wiring status, phase by phase, with what recomputes each item |
| `CAPABILITY_ASSESSMENT.md` | what the machine can do, measured rather than described |
| `ANALOGY_LAYER_STUDY.md` | analogy by named relation |
| `GEOMETRIC_AMBIGUITY_STUDY.md` | the six-fold Golay tie, bundling, collapse, and the chain's dynamics |
| `INFINITE_VALUES_STUDY.md` | reals as processes, and where the value layer stops |
| `INFORMATION_LOSS_STUDY.md` | what a layer boundary costs, made precise enough to prove |
| `overlay/FIGURES.md` | **generated** — every documented count, recomputed |
| `overlay/README.md` | the package repository's own top-level README, with the archival change log |
