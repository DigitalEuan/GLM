# Round 8: supporting files (outside Lean)

The formal result of this round is in the Lean package:
`RequestProject/GLM/Rule30/TopMonomial.lean`. It proves that `whiteDiagonalCount n` is odd for
every `n ≥ 2`, so `deg a(n)(c) = 2n − 1` holds for every `n ≥ 2` and every cell `c`. See
"Round 8" in the package README. This folder holds only the GLM wiring for the round, and
nothing in it is a proof.

## The files you attached

* `__init__.py` is the real `glm_universal/runtime/reports/__init__.py`. It replaces the Round 7
  shim (`rule30_round7/glm_reports_init_shim.py`), which is no longer needed.
* `LatticeGeometryReports` is **not** defined in `session.py`. That file only imports it, through
  `from .reports import (..., LatticeGeometryReports, ...)`. Your `__init__.py` takes the class
  from `from .lattice_geometry import LatticeGeometryReports`, so the missing piece is the single
  module `glm_universal/runtime/reports/lattice_geometry.py`. That module is not in
  `glm_repo.zip`.
* `lattice_geometry_standin.py` is a stand-in for that one module. It defines
  `LatticeGeometryReports` with the 14 `_report_*` methods the session dispatcher calls:
  `deep_holes`, `facets`, `fusion`, `hole_classifier`, `hole_configuration`, `hole_failures`,
  `hole_ladder`, `lattices`, `llvq`, `monster_stack`, `multiresolution`, `shells`, `subalgebra`
  and `transform_decoder`. Each method refuses with an error that names the missing file. For
  example, `report facets` returns "report subject unavailable:
  glm_universal/runtime/reports/lattice_geometry.py is not in this checkout". **Replace it with the
  real file from your repository.**

## Setup used

```
cp parser.py session.py tct_engine.py      glm_universal/runtime/
cp __init__.py                             glm_universal/runtime/reports/__init__.py
cp rule30_round8/lattice_geometry_standin.py glm_universal/runtime/reports/lattice_geometry.py
PYTHONPATH=. python3 rule30_round7/glm_probe.py > rule30_round8/glm_probe_output_round8.txt
```

## What the GLM said (`glm_probe_output_round8.txt`)

The answers match Round 7:

* The session still refuses the Rule 30 questions, because no enabled domain contains a
  cellular-automaton carrier.
* Its own reports work. Golay decoding reports 4096 cosets with unique decoding below weight 4.
  `report capabilities` reports 33 probes: 20 hold and 13 break.

## Following the GLM's lead

The GLM refuses Rule 30 queries because it has no carrier for "cellular automaton", "centre
column" or "light-cone triangle". This round's Lean proof suggests what such a register would
need to hold:

* a **triangle carrier** with two boundary sides (left `l`, right `r`);
* the **peel-two move**, which removes the two leftmost cells and maps a GF(2) functional of the
  triangle to a functional of a triangle one size smaller (coefficients go to prefix sums);
* the **invariant** that survives the move, `Σ (γ + β·l) ≡ β_0`.

That combination of a carrier, a move and an invariant fits the GLM's existing substrate style:
it is exact, finite, and does not carry an infinite value. It would be a natural first Rule 30
register.
