"""GLM-3+ -- the Universal MOG-Cube Geometric Language Machine.

A self-contained, exact, deterministic implementation of the geometric
substrate the Monster group actually acts on, and of the reasoning layers
built on top of it.

Layers
------
``glm_universal.substrate``
    Step 1 (implemented).  The Leech lattice, ``Lambda / 2 Lambda``, the MOG
    trio and sextet, and the 10-plane 2-adic digit stack.
``glm_universal.data_objects``
    Step 2 (implemented).  Typed carriers that wrap arbitrary data as substrate
    points: 660 physical quantities in SI7 and EXT10, all 118 chemical
    elements, rational matrices and exact reflections, and relational lexical
    concepts -- each with a dynamically fitted 2-adic digit stack.
``glm_universal.reasoning``
    Step 3 (implemented).  The Norton-Sakuma ``2A`` product algebra over the
    substrate's type-2 classes, the positive-definite Griess metric with exact
    rational clustering, proportional analogy with exact nearest-point
    decoding in ``Lambda``, and the multi-plane audit of the register's
    physical relations with 31-facet failure attribution.
``glm_universal.runtime``
    Step 4 (implemented).  The interactive runtime: deterministic semantic
    query parsing, the stateful :class:`~glm_universal.runtime.session.
    GeometricSession` over all five registers, and the Three Column Thinking
    engine whose third column is a generated script that re-derives the answer
    in a fresh interpreter and asserts it against the second column.
``glm_universal.benchmarks``
    Reserved.  Task suites and scoring.

Design invariants, enforced package-wide
----------------------------------------
* **Exact arithmetic only.**  ``int`` and ``fractions.Fraction``.  No float
  ever touches a quantity that feeds a result; :func:`~glm_universal.
  substrate.digit_stack.class_stack` rejects floats with a ``TypeError``.
* **No randomness.**  ``random`` is not imported anywhere in the package.
  Every function is a deterministic function of its arguments.
* **Standard library only.**  No third-party runtime dependency.
* **Facts are computed, not quoted.**  Codeword counts, class censuses and
  Witt data are recomputed by ``*_report`` functions on demand.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__", "substrate", "data_objects", "reasoning", "runtime"]

from . import substrate  # noqa: E402
from . import data_objects  # noqa: E402
from . import reasoning  # noqa: E402
from . import runtime  # noqa: E402
