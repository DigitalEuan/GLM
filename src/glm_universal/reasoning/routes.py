"""``glm_universal.reasoning.routes`` -- choosing a method at a decision
point by what can be decided about the problem in hand (sharpening pass
after Phase 108).

Why it exists
-------------
Several rounds added a second or third method to a step and shipped it behind
a module switch (``symbolic_nonlinear.TRIG`` and the like).  A switch is the
right instrument for a measurement -- the round reads every text with it off
and on and shows nothing else moved -- but it is the wrong way for the machine
to *use* a method: a switch is global, it cannot say *why* a method was taken,
and it cannot take two methods at once when the problem does not decide
between them.

This module is the small piece that replaces the switch as the way a route is
reached.  A decision point names its candidate routes; each candidate carries
the fact that makes it sound here, decided from the problem (a discriminant
plainly negative, a symmetric definite pencil, ...).  :func:`choose` takes
the first candidate whose fact holds, records the decision with its reason,
and the caller writes the reason into the derivation steps, so column 2 says
which route was taken and why.

Two inputs steer it without touching the code of the decision point:

* :data:`DISABLED` -- route names switched off for a measurement (the old
  switches set and clear these, so an A/B reading is still one line);
* :func:`facts` -- a context in which a caller states what it knows about
  the problem that the solver cannot see (the equations of motion know that
  ``det(K - w^2 M)`` comes from a symmetric definite pair, so every root is
  real; the solver, handed only the polynomial, does not).

Nothing here computes; every route's soundness is the route's own (its Lean
file is named at the decision point).
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Tuple

__all__ = ["Decision", "DISABLED", "POINTS", "DECIDERS", "choose", "facts",
           "fact", "trace", "describe", "disabled", "as_shipped",
           "decider_on", "report"]


@dataclass(frozen=True)
class Decision:
    point: str
    route: str
    why: str

    def text(self) -> str:
        return f"route {self.route} at {self.point}: {self.why}"


#: Route names switched off (``"point:route"``) -- for measurement only.
DISABLED: set = set()

#: Every decision point and its routes, in the order they are tried, with
#: the condition each needs: the documentation ``describe`` prints.
POINTS: Dict[str, List[Tuple[str, str]]] = {
    "cubic.letters": [
        ("viete", "the three roots are known to be real: the discriminant "
                  "is plainly negative, or the caller states real roots "
                  "(a symmetric definite pencil); "
                  "RequestProject/GLM/CubicTrig.lean"),
        ("cardano", "the discriminant is plainly positive, so one real "
                    "root; RequestProject/GLM/CubicRadicals.lean"),
        ("cases", "the sign of the discriminant is not decided: both "
                  "regimes, each under its own condition (D > 0 Cardano, "
                  "D < 0 Viete)"),
    ],
    "modes.cubic": [
        ("stepwise", "the characteristic cubic of a symmetric definite "
                     "pair in letters: the roots are named through the "
                     "coefficients (P, Q, K in turn), all real and positive "
                     "by Sylvester's criterion, checked by Sturm"),
        ("solver", "otherwise: the characteristic equation goes to the "
                   "branch layer"),
    ],
    # Phase 109: four or more degrees of freedom
    "modes.higher": [
        ("ferrari", "a characteristic quartic of a symmetric definite pair "
                    "(four degrees of freedom): the depressed quartic, its "
                    "resolvent cubic (three real roots z = (y_i + y_j)^2, "
                    "named by Viete as at modes.cubic) and the four roots "
                    "from their square roots; "
                    "RequestProject/GLM/QuarticResolvent.lean"),
        ("named", "a characteristic polynomial of degree five or more of a "
                  "symmetric definite pair: no general radical form exists, "
                  "so the roots are named -- all real and positive, their "
                  "sum and product read off the coefficients, their count "
                  "checked by Sturm"),
        ("solver", "otherwise (the mass matrix is not plainly definite): "
                   "the characteristic equation goes to the branch layer"),
    ],
}

#: How a fact a decision point rests on is decided, in the order tried --
#: a decider can be switched off like a route (``"point:decider"`` in
#: :data:`DISABLED`), so a round measured before it existed still reads its
#: own code.
DECIDERS: Dict[str, List[Tuple[str, str]]] = {
    "cubic.letters": [
        ("surface", "the expanded discriminant is plainly signed: every "
                    "term an even power with a positive coefficient (or "
                    "every term of minus it)"),
        ("factor", "Phase 109: the discriminant split into a constant and "
                   "square-free factors (Yun); a factor to an even power is "
                   ">= 0 and every factor to an odd power is plainly "
                   "signed; reasoning/sign_factor.py, "
                   "RequestProject/GLM/SignFactor.lean"),
    ],
}


def decider_on(point: str, name: str) -> bool:
    """Whether the decider ``name`` of ``point`` is in use."""
    return f"{point}:{name}" not in DISABLED

_TRACE: List[Decision] = []
_FACTS: List[Dict[str, object]] = [{}]


def choose(point: str, candidates: Sequence[Tuple[str, bool, str]]
           ) -> Optional[Decision]:
    """The first ``(route, holds, why)`` whose fact holds and whose route is
    not disabled; ``None`` when none applies.  The decision is recorded."""
    for route, holds, why in candidates:
        if holds and f"{point}:{route}" not in DISABLED:
            d = Decision(point, route, why)
            _TRACE.append(d)
            del _TRACE[:-64]
            return d
    return None


def trace() -> List[Decision]:
    """The most recent decisions, oldest first (at most 64)."""
    return list(_TRACE)


@contextmanager
def facts(**known: object) -> Iterator[None]:
    """State facts about the problem for the decision points reached inside
    the block (nested blocks add to the outer ones)."""
    _FACTS.append({**_FACTS[-1], **known})
    try:
        yield
    finally:
        _FACTS.pop()


def fact(name: str, default: object = None) -> object:
    return _FACTS[-1].get(name, default)


@contextmanager
def disabled(*names: str) -> Iterator[None]:
    """Routes (``"point:route"``) switched off inside the block only."""
    added = [n for n in names if n not in DISABLED]
    DISABLED.update(added)
    try:
        yield
    finally:
        DISABLED.difference_update(added)


def as_shipped(*names: str) -> Callable:
    """Decorate a round's measurement so it reads the code as the round
    shipped it: the later routes ``names`` are disabled while it runs.  A
    round's declared marks stay a statement about that round."""
    def wrap(fn: Callable) -> Callable:
        @wraps(fn)
        def inner(*a, **k):
            with disabled(*names):
                return fn(*a, **k)
        return inner
    return wrap


def describe() -> str:
    lines = []
    for point, rows in POINTS.items():
        lines.append(point)
        for route, cond in rows:
            off = " (disabled)" if f"{point}:{route}" in DISABLED else ""
            lines.append(f"  {route}{off}: {cond}")
        for name, how in DECIDERS.get(point, ()):
            off = "" if decider_on(point, name) else " (disabled)"
            lines.append(f"  decided by {name}{off}: {how}")
    return "\n".join(lines)


def report() -> Dict[str, object]:
    """Every decision point, its routes in the order tried with the
    condition each needs, the deciders, what is switched off, and the
    decisions most recently taken -- the ``report routes`` subject."""
    points = []
    for point, rows in POINTS.items():
        points.append({
            "point": point,
            "routes": [{"route": r, "condition": c,
                        "disabled": f"{point}:{r}" in DISABLED}
                       for r, c in rows],
            "deciders": [{"decider": n, "how": h,
                          "disabled": not decider_on(point, n)}
                         for n, h in DECIDERS.get(point, ())],
        })
    return {
        "points": points,
        "routes": sum(len(p["routes"]) for p in points),
        "disabled": sorted(DISABLED),
        "recent": [{"point": d.point, "route": d.route, "why": d.why}
                   for d in _TRACE],
    }
