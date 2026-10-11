"""``glm_universal.runtime.route_report`` -- the ``report routes`` subject
(Phase 109).

Since the sharpening pass after Phase 108 the machine chooses a method at a
decision point by what it can decide about the problem in hand
(:mod:`glm_universal.reasoning.routes`), and writes the choice and its reason
into column 2 of the answer it gives.  Column 2 is the only place a choice
showed, so the question *which routes are there, and which does each kind of
problem take?* had no answer short of asking every kind of problem.

This module answers it in one place:

* every decision point, its routes in the order they are tried, the
  condition each needs, and how a fact it rests on is decided
  (:data:`~glm_universal.reasoning.routes.DECIDERS`);
* what is switched off (a measurement's A/B reading), if anything;
* the decision each **reference problem** takes, computed live -- one
  problem per route that has one, so a route that stops being reached shows
  as a changed row rather than as silence.

Nothing here decides a route; it asks the decision points and reports.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

__all__ = ["REFERENCE", "reference_decisions", "route_report"]

#: ``(point, problem, kind, expected route)`` -- the reference problems.
#: ``kind`` is ``"cubic"`` (an equation for ``x``), ``"chain:N:..."`` (the
#: small oscillations of an ``N``-link chain pendulum, identical or not) or
#: ``"lagrangian:q1,q2,..."`` (the small oscillations of the Lagrangian the
#: problem states).
REFERENCE: Tuple[Tuple[str, str, str, str], ...] = (
    ("cubic.letters", "x^3 + p*x = q", "cubic", "cases"),
    ("cubic.letters", "x^3 + 3*(a - b)^2*x = 2*(a - b)^3", "cubic",
     "cardano"),
    ("cubic.letters", "x^3 - (a^2 + a*b + b^2)*x + a*b*(a + b) = 0", "cubic",
     "viete"),
    ("cubic.letters", "x^3 - 3*s^2*x + s^3 = 0", "cubic", "viete"),
    ("modes.cubic", "triple pendulum, masses m1..m3, lengths l1..l3",
     "chain:3:unequal", "stepwise"),
    ("modes.cubic", "identical triple pendulum", "chain:3:identical",
     "solver"),
    ("modes.higher", "quadruple pendulum, masses m1..m4, lengths l1..l4",
     "chain:4:unequal", "ferrari"),
    ("modes.higher", "identical quintuple pendulum", "chain:5:identical",
     "named"),
    ("modes.higher", "L = (1/2)*(a - b)*x1_dot^2 + (1/2)*x2_dot^2 + "
                     "(1/2)*x3_dot^2 + (1/2)*x4_dot^2 - (1/2)*k*(x1^2 + "
                     "x2^2 + x3^2 + x4^2)", "lagrangian:x1,x2,x3,x4",
     "solver"),
)


def _decide(point: str, problem: str, kind: str) -> List[Dict[str, str]]:
    """Run one reference problem and return the decisions it took at
    ``point`` (normally one; a case split may take several)."""
    from ..reasoning import routes as R
    from ..reasoning import symbolic as S
    before = len(R.trace())
    try:
        if kind == "cubic":
            from ..reasoning.symbolic_nonlinear import solve_nonlinear
            text = problem if "=" in problem else problem + " = 0"
            lhs, rhs = S.parse_equation(text, S.Context())
            solve_nonlinear([(lhs, rhs)], {"x"}, ["x"], extended=True)
        elif kind.startswith("lagrangian:"):
            from ..reasoning import derivation as D
            coords = kind.split(":", 1)[1].split(",")
            D.equations_of_motion(problem.split("=", 1)[1].strip(), coords,
                                  True)
        else:
            from ..reasoning import derivation as D
            from .derivation_frames import chain_lagrangian
            _, n, same = kind.split(":")
            n = int(n)
            masses = ["m"] * n if same == "identical" else \
                [f"m{i + 1}" for i in range(n)]
            lengths = ["l"] * n if same == "identical" else \
                [f"l{i + 1}" for i in range(n)]
            D.equations_of_motion(chain_lagrangian(n, masses, lengths),
                                  [f"th{i + 1}" for i in range(n)], True)
    except S.SymbolicError as exc:
        return [{"route": "(refused)", "why": f"{exc.code}: {exc.why}"}]
    taken = R.trace()[before:] if len(R.trace()) > before else []
    # the trace keeps at most 64 decisions; a problem takes a handful
    return [{"route": d.route, "why": d.why} for d in taken
            if d.point == point]


def reference_decisions() -> List[Dict[str, object]]:
    """Every reference problem with the route it took and why."""
    out = []
    for point, problem, kind, expected in REFERENCE:
        got = _decide(point, problem, kind)
        routes = sorted({g["route"] for g in got})
        out.append({"point": point, "problem": problem,
                    "expected": expected,
                    "taken": ",".join(routes) or "(no decision)",
                    "why": got[0]["why"] if got else "",
                    "as_expected": routes == [expected]})
    return out


def route_report() -> Dict[str, object]:
    """The decision points, their routes and deciders, what is disabled,
    and the reference problems' decisions."""
    from ..reasoning import routes as R
    base = R.report()
    refs = reference_decisions()
    reached = {(r["point"], r["taken"]) for r in refs}
    unreached = [f"{p['point']}:{rt['route']}" for p in base["points"]
                 for rt in p["routes"]
                 if (p["point"], rt["route"]) not in reached]
    return {
        "points": base["points"],
        "point_count": len(base["points"]),
        "route_count": base["routes"],
        "disabled": base["disabled"],
        "reference": refs,
        "reference_count": len(refs),
        "as_expected": sum(1 for r in refs if r["as_expected"]),
        "unreached": unreached,
        "holds": all(r["as_expected"] for r in refs),
    }
