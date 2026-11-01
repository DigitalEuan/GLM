"""STAND-IN for ``glm_universal/runtime/reports/lattice_geometry.py`` (Round 8).

The real module is not in ``glm_repo.zip``.  The ``reports/__init__.py`` you supplied imports
``LatticeGeometryReports`` from ``.lattice_geometry``, and ``session.py`` only *imports* the
class (it does not define it).  This stand-in defines the class with the fourteen
``_report_*`` methods the session dispatcher calls; each one refuses with a ``SolverError``
that names the missing file, so the session imports and every other subject works, and a
lattice-geometry subject fails loudly instead of silently.

Replace this file with the real ``lattice_geometry.py`` from your GLM repository.
"""
from __future__ import annotations

from ..parser import Query
from ..solution import Solution, SolverError

_MISSING = ("report subject unavailable: glm_universal/runtime/reports/lattice_geometry.py "
            "is not in this checkout (stand-in module loaded)")


class LatticeGeometryReports:
    """Stand-in mixin; holds no state.  Every method refuses."""

    def _report_deep_holes(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [deep_holes]")

    def _report_facets(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [facets]")

    def _report_fusion(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [fusion]")

    def _report_hole_classifier(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [hole_classifier]")

    def _report_hole_configuration(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [hole_configuration]")

    def _report_hole_failures(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [hole_failures]")

    def _report_hole_ladder(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [hole_ladder]")

    def _report_lattices(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [lattices]")

    def _report_llvq(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [llvq]")

    def _report_monster_stack(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [monster_stack]")

    def _report_multiresolution(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [multiresolution]")

    def _report_shells(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [shells]")

    def _report_subalgebra(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [subalgebra]")

    def _report_transform_decoder(self, query: Query) -> Solution:
        raise SolverError(_MISSING + " [transform_decoder]")
