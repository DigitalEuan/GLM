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
    points: 726 physical quantities in SI7 and EXT10, all 118 chemical
    elements, rational matrices and exact reflections, and relational lexical
    concepts -- each with a dynamically fitted 2-adic digit stack.
``glm_universal.reasoning``
    Step 3 (implemented).  The Norton-Sakuma ``2A`` product algebra over the
    substrate's type-2 classes, the positive-definite Griess metric with exact
    rational clustering, proportional analogy with exact nearest-point
    decoding in ``Lambda``, and the multi-plane audit of the register's
    physical relations with 31-facet failure attribution.
``glm_universal.semantics``
    Step 3b (implemented).  The meaning space: what a term denotes, encoded
    as 24 exact rationals with no dependence on how it is spelled; reference
    resolution from notation to meaning with an explicit refusal where no
    determinate referent exists; relations derived from meanings and
    re-checkable from them; and the audit of the inherited concept graph
    against all of it.
``glm_universal.recipe``
    Step 3c (implemented).  The recipe made into an object: a declarative
    description of a domain -- its objects, which held quantity each
    coordinate derives from, what a reading of one object is, and what must be
    refused -- and one generic path from such a description to the carrier
    encoding, the layer chain, the widening audit, the query surface and the
    refusal boundary.  Three domains built by hand in earlier rounds are
    deleted and regenerated from their descriptions, with their measured
    figures unchanged.
``glm_universal.language``
    Step 3d (implemented).  The surface language made an object: a
    declarative description of a *question* -- an opening, named slots, the
    words that separate them, and the boundaries it refuses at -- and one
    generic matcher that reads any of them.  Three of the runtime's query
    kinds are described this way, and the described shapes are measured
    against the hand-written parser over a corpus generated from the
    registers: the same kind and the same options, question by question.
``glm_universal.runtime``
    Step 4 (implemented).  The interactive runtime: deterministic semantic
    query parsing, the stateful :class:`~glm_universal.runtime.session.
    GeometricSession` over all six registers, and the Three Column Thinking
    engine whose third column is a generated script that re-derives the answer
    in a fresh interpreter and asserts it against the second column.
``glm_universal.migration``
    Step 5 (implemented).  The bridge to the repository's persisted data: the
    frame and bit-order determination, the exact migration of the stored
    concept / CRG-edge / hexcolour state into canonical form, and the store
    that answers questions of the migrated payload.
``glm_universal.benchmarks``
    Step 6 (implemented).  Scored task suites with declared evidence tiers,
    published baselines, and findings -- including null and negative results
    -- reported beside the scores.  Imported lazily, because a suite pulls in
    the runtime.
``glm_universal.capabilities``
    Step 7 (implemented).  Capability probes: what the machine can do at all,
    and -- for each thing it cannot -- the exact place it stops.  A probe that
    ``breaks`` is a located boundary, not a failure; several of those
    boundaries are theorems.  Imported lazily, like the benchmarks.
``glm_universal.evaluation``
    Step 8 (implemented).  The end-to-end assessment: a fixed question set
    across every query kind and report subject, driven through ``GLM.py`` in a
    fresh interpreter and scored automatically, with a confident wrong answer
    counted as a worse failure than a refusal.  Imported lazily.
``glm_universal.signoff``
    Step 9 (implemented).  The sign-off ledger: for each test file, a digest
    of everything it depends on, so a unit that has not changed since it last
    passed need not be run again -- and, more importantly, a unit that *has*
    changed cannot be reported as green.  ``glm_universal.integrity`` is the
    one place in the package that computes a digest at all, and
    ``glm_universal.tools`` is the command line for the study instruments.
    None of the three is on the answering path.

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

__version__ = "1.15.0"

__all__ = ["__version__", "substrate", "data_objects", "reasoning",
           "semantics", "recipe", "language", "runtime", "migration",
           "benchmarks", "capabilities", "evaluation"]

from . import substrate  # noqa: E402
from . import data_objects  # noqa: E402
from . import reasoning  # noqa: E402
from . import semantics  # noqa: E402
from . import recipe  # noqa: E402
from . import language  # noqa: E402
from . import runtime  # noqa: E402
from . import migration  # noqa: E402


def __getattr__(name: str):
    """Resolve ``glm_universal.benchmarks`` on first use.

    The benchmark suites import the runtime, and the runtime's ``report
    benchmarks`` solver imports the benchmarks, so binding the subpackage
    eagerly here would close a cycle.  Deferring it to attribute access keeps
    ``from glm_universal import benchmarks`` working without one.
    """
    if name in ("benchmarks", "capabilities", "evaluation"):
        import importlib
        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
