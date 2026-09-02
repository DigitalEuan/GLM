"""``glm_universal.runtime.payload`` -- rendering a report for JSON.

A solver's ``payload`` has to survive ``json.dumps``, and the values the
reasoning modules return do not: they are exact :class:`~fractions.Fraction`\\
s, sometimes with hundreds of digits above and below the line.  The four
renderers here are the package's answer, and none of them constructs a float:
a rational becomes either its ``"n/d"`` string or a scientific-notation
rendering to a stated number of digits, and the exact value stays in the
module that produced it.

They sit here rather than in :mod:`~glm_universal.runtime.session` because
both the session and the report families in
:mod:`glm_universal.runtime.reports` use them, and this module imports
neither.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, Mapping, Optional

from ..reasoning import wobble as wbl
from .solution import q

__all__ = ["as_magnitude", "containers_payload", "drift_payload",
           "noise_payload", "jsonable"]


def as_magnitude(text: str) -> Optional[Fraction]:
    """Read a written magnitude exactly, or return ``None`` if it is a word.

    Accepts an integer, a decimal string and a fraction, and a trailing unit
    symbol is tolerated -- ``\"300 K\"`` is the magnitude 300.  No float is
    constructed: the decimal string goes straight to :class:`Fraction`.
    """
    body = text.strip()
    if not body:
        return None
    head = body.split()[0]
    try:
        return Fraction(head)
    except (ValueError, ZeroDivisionError):
        return None


def containers_payload(report: Mapping[str, Any]) -> Dict[str, object]:
    """Render the containers report so ``json.dumps`` accepts it.

    Liouville's reference carries a denominator of ten to the seven hundred
    and twentieth, and the projection squares it, so every rational in the
    payload is rendered in scientific notation and the exact values are left
    in the module where :mod:`~glm_universal.reasoning.containers` returns
    them unrounded.
    """
    def render(value: Any) -> Any:
        if isinstance(value, Fraction):
            return wbl.sci_str(value, 6)
        if isinstance(value, dict):
            return {str(k): render(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [render(v) for v in value]
        return value
    return {k: render(v) for k, v in report.items()}


def drift_payload(report: Mapping[str, Any]) -> Dict[str, object]:
    """Render the drift report so ``json.dumps`` accepts it.

    The exact columns of the drift table are rationals whose numerator and
    denominator run to hundreds of digits, so the payload carries the
    scientific-notation rendering of each and leaves the exact values in the
    module, where :func:`drift.drift_table` returns them unrounded.
    """
    def render(value: Any) -> Any:
        if isinstance(value, Fraction):
            return wbl.sci_str(value, 4)
        if isinstance(value, dict):
            return {k: render(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [render(v) for v in value]
        return value
    return {k: render(v) for k, v in report.items()}


def noise_payload(report: Mapping[str, Any]) -> Dict[str, object]:
    """Render the noise report so ``json.dumps`` accepts it."""
    def render(value: Any) -> Any:
        if isinstance(value, Fraction):
            return q(value)
        if isinstance(value, dict):
            return {k: render(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [render(v) for v in value]
        return value
    return {k: render(v) for k, v in report.items()}


def jsonable(mapping: Mapping[str, Any]) -> Dict[str, object]:
    """Render an attribute mapping so ``json.dumps`` accepts it.

    Rationals become ``"n/d"`` strings rather than floats, which is the only
    lossless option and the one the whole package uses.
    """
    out: Dict[str, object] = {}
    for key, value in sorted(mapping.items()):
        if isinstance(value, Fraction):
            out[key] = q(value)
        elif isinstance(value, (list, tuple)):
            out[key] = [q(x) if isinstance(x, Fraction) else x for x in value]
        elif isinstance(value, (int, str, bool)) or value is None:
            out[key] = value
        else:
            out[key] = repr(value)
    return out
