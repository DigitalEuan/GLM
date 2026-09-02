"""``glm_universal.runtime.solution`` -- what a solver returns.

The three carriers every solver in the package builds -- a :class:`Step`, a
:class:`Solution` and the :class:`InferenceRecord` the session keeps in its
history -- together with :class:`SolverError` and the canonical rendering
:func:`q` of an exact scalar.

Why they live here rather than in :mod:`~glm_universal.runtime.session`
-----------------------------------------------------------------------
The report solvers moved out of the session into
:mod:`glm_universal.runtime.reports`, one module per family.  Those modules
build :class:`Solution`\\ s, and the session imports them to mix them into
:class:`~glm_universal.runtime.session.GeometricSession`, so the carriers
have to sit *below* both: this module imports the parser and nothing else of
the package, which makes the import order a line rather than a cycle.

Every name here is re-exported from
:mod:`~glm_universal.runtime.session`, so ``from ...session import Solution``
keeps working and no caller had to change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Dict, Mapping, Optional, Tuple

from .parser import Query

__all__ = ["SolverError", "Step", "Solution", "InferenceRecord", "q"]


class SolverError(ValueError):
    """Raised when a well-formed query cannot be solved as asked.

    Distinct from :class:`~glm_universal.runtime.parser.QueryError`, which is
    about the shape of the string.  This is about the content: an operand that
    names nothing in the register, a domain with no candidate pool, a class
    label that is not of type 2.
    """


def q(x: Any) -> str:
    """Canonical ``"n/d"`` rendering of an exact scalar.

    Every rational that crosses a module boundary in this package is written
    this way -- in ``expected``, in the generated script, and in the JSON
    export -- so that comparing two of them is a string comparison that cannot
    silently succeed on a rounded value.
    """
    f = Fraction(x)
    return f"{f.numerator}/{f.denominator}"


@dataclass(frozen=True)
class Step:
    """One reasoning step, stated twice: in language and in exact algebra.

    Attributes
    ----------
    label
        A short stable identifier for the step, so a test can assert on the
        presence of a step without matching prose.
    language
        Column 1: what this step does and why, in plain English.
    mathematics
        Column 2: the same step as an exact statement over ``Q``, ``Z`` or
        ``F_2``.  Never an approximation and never a float.
    """

    label: str
    language: str
    mathematics: str

    def as_dict(self) -> Dict[str, str]:
        """A JSON-serialisable view."""
        return {"label": self.label, "language": self.language,
                "mathematics": self.mathematics}


@dataclass(frozen=True)
class Solution:
    """What a solver returns: an answer plus everything needed to check it."""

    query: Query
    kind: str
    answer: str
    steps: Tuple[Step, ...] = ()
    expected: Mapping[str, str] = field(default_factory=dict)
    script_spec: Mapping[str, object] = field(default_factory=dict)
    payload: Mapping[str, object] = field(default_factory=dict)
    ok: bool = True
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "query": self.query.as_dict(),
            "kind": self.kind,
            "answer": self.answer,
            "steps": [s.as_dict() for s in self.steps],
            "expected": dict(self.expected),
            "script_spec": dict(self.script_spec),
            "payload": dict(self.payload),
            "ok": self.ok,
            "error": self.error,
        }


@dataclass(frozen=True)
class InferenceRecord:
    """One entry of the session's history."""

    index: int
    raw_query: str
    kind: str
    domain: Optional[str]
    answer: str
    ok: bool

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {"index": self.index, "raw_query": self.raw_query,
                "kind": self.kind, "domain": self.domain,
                "answer": self.answer, "ok": self.ok}
