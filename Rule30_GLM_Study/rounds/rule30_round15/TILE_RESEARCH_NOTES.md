# What we took from the aperiodic-tiling research

## Source

This note replaces the attached material. The package does not include the PDFs or the Lean
file. The citation is:

* Conor Grogan, *Aperiodic Monotiles in Every Dimension*, manuscript, revision of 22 October 2026,
  with the earlier "working v1" draft. The manuscript attributes the general keyed-product idea to
  Adam Scherlis ("Monotiles in every dimension").
* Its companion Lean file `PalomarAllDimensionsSolution.lean.txt`, a reconstructed source dated
  18 October 2026.

The status of the source, as it reports itself:

* The manuscript says that final independent kernel checking and the axiom audit of the
  all-dimensional theorem are still pending.
* The Lean file imports a module (`NativeFinalAssembly.AllDimensions`) that was not supplied, so
  it cannot be compiled here.
* Nothing in this package imports or depends on it.

We took **ideas**, not results.

## The four ideas and what became of them

| Idea in the tiling work | Rule 30 counterpart | Outcome |
|---|---|---|
| A *period* is a translation of the **whole tile collection**. Testing only the union is vacuous. | A period of the whole space-time diagram, as opposed to a period of one column (Problem 1) | Proved: the seed's diagram has no non-trivial eventual translation (`seed_spacetime_period_trivial`). This is easy. The prize problem asks for rigidity of one *projection*, which is the hard part. |
| *Finite linear image controls the symmetry group* (Lemma 7.1): if translations are trivial, a symmetry is fixed by its linear part. | The linear parts of the line's isometries are `+1` and the mirror `-1` | Proved: the mirror is excluded too (`seed_no_mirror_symmetry`). So the eventual symmetry group is trivial. |
| *Boundary keys* break symmetry, and *local forcing* on a finite region (the "parent occurrence" premise) feeds an induction. | The left edge of a left-white row is the key. Rule 30's local rule forces cells next to a periodic column. | Proved: `key_forcing` for every run, and the **period-2 forcing lemma** (`alt_pair_constant`, `alt_shift_complement`, `alt_left_determined`). These reduce the first open rung of Problem 1 to one half-speed sequence. No induction closing it was found. |
| *Marked → unmarked bridge*: aperiodicity of decorated tiles transfers to bare tiles when the decoration is **recognizable** from the shape. Product aperiodicity is proved by projecting periods to the factors. | Adjacent column pairs are proved aperiodic (the "marked" object). The bare centre column is the unmarked one. | Proved: if a neighbour column is a sliding-window function of the centre column, Problem 1 follows (`problem1_of_neighbour_recognizable`). The data (EMP) do not support recognizability: about 0.3 bits remain uncertain. |

## What the tiling research does not offer

* **Hierarchy / substitution.** Tiling aperiodicity proofs end with a self-similar hierarchy that
  is forced at every scale. No such hierarchy is known for Rule 30. The period-2 forcing lemma
  is the closest analogue found, and it does not recurse cleanly: column `c - 4` is a nonlinear
  function of the half-speed sequence (see `r15_alt_reduction_output.txt`).
* **Problems 2 and 3.** Tiling theory proves "no period" statements. It says nothing about
  frequencies (P2) or running-time lower bounds (P3).
* **Direction of the product theorem.** Tilings prove *factor aperiodic ⇒ product aperiodic*.
  Rule 30 needs the converse, *pair aperiodic ⇒ single column aperiodic*, which only holds with
  extra structure such as recognizability.
