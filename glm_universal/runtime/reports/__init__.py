"""``glm_universal.runtime.reports`` -- the ``report <subject>`` solvers.

Every report subject recomputes its facts on demand: nothing here quotes a
number, and each solver returns a :class:`~glm_universal.runtime.solution.
Solution` whose ``expected`` mapping is checked in a fresh interpreter by
Three Column Thinking.  What changed in v1.12.0 is only *where* they live.

Why they moved
--------------
They were all methods of
:class:`~glm_universal.runtime.session.GeometricSession`, and the session had
grown to eight and a half thousand lines, of which forty-eight hundred were
report solvers.  Every round that added a capability added a subject, so the
one file grew monotonically and the dispatcher -- the part a reader actually
needs when following a query -- was buried in the middle of it.

Each module here holds one family, named for what computes it, so a subject
sits beside a docstring that says which sub-package it reads and a reader
looking for the harmonic report does not have to walk past the Leech theta
series to reach it.  The classes are mixins with no state of their own;
``GeometricSession`` inherits all eleven, so ``self`` is the session and no
call site, template or test had to change.

The families
------------
=========================  ==================================================
module                     subjects
=========================  ==================================================
``substrate``              leech distribution, theta, golay decoding,
                           superposition, leech construction
``lattice_geometry``       subalgebra, fusion, facets, monster stack,
                           multiresolution, deep holes, lattices, shells,
                           transform decoder
``registers``              relations, units, molecules, chemistry coverage,
                           harmony, economics, analogies
``resolution``             information loss, escalation, names, measure
``signal``                 noise, signature, drift, containers, mantissa,
                           reversible, engine, infinite values
``ledgers``                blueprint, catalog, companion, capabilities,
                           benchmarks
``semantics``              semantics
``migration``              migration, state migration, concept store
``development``            lean, directives, pipeline
``recipe``                 recipe
``language``               language
=========================  ==================================================

The import direction is unchanged and still one-way: a report module imports
the sub-package that computes its subject, the parser and
:mod:`~glm_universal.runtime.solution`; no sub-package imports a report
module.  :data:`~glm_universal.runtime.session.REPORT_SUBJECTS` remains the
one list of subject names, and ``_solve_report`` in the session remains the
one dispatcher.
"""
from __future__ import annotations

from .development import DevelopmentReports
from .language import LanguageReports
from .lattice_geometry import LatticeGeometryReports
from .ledgers import LedgerReports
from .migration import MigrationReports
from .recipe import RecipeReports
from .registers import RegisterReports
from .resolution import ResolutionReports
from .semantics import SemanticsReports
from .signal import SignalReports
from .substrate import SubstrateReports

#: The mixins, in the order :class:`GeometricSession` inherits them.
REPORT_MIXINS = (
    SubstrateReports,
    LatticeGeometryReports,
    RegisterReports,
    ResolutionReports,
    SignalReports,
    LedgerReports,
    SemanticsReports,
    MigrationReports,
    DevelopmentReports,
    RecipeReports,
    LanguageReports,
)

__all__ = [
    "DevelopmentReports", "LanguageReports", "LatticeGeometryReports",
    "LedgerReports", "MigrationReports", "RecipeReports", "RegisterReports",
    "ResolutionReports", "SemanticsReports", "SignalReports",
    "SubstrateReports", "REPORT_MIXINS",
]
