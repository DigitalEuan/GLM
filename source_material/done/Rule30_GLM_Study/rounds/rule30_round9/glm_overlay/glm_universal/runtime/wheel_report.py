"""``glm_universal.runtime.wheel_report`` -- answers about the automata register ("the Wheel").

Two entry points, both called from :class:`~glm_universal.runtime.session.GeometricSession`:

* :func:`describe` -- ``describe <automata carrier>``: the carrier's exact statement, its
  evidence class and Lean reference, an independent recomputation where one is finite, and
  the boundary of what the carrier establishes.
* :func:`report_wheel` -- ``report wheel``: the family census and the status of the three
  questions for wheel ``00011110`` from the impulse row.

Every step is written twice, as the rest of the session writes them: in words and in exact
mathematics.  Nothing is rounded.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Dict, List

from ..data_objects import automata as ca
from ..data_objects.base import DataObject
from .parser import Query
from .solution import Solution, Step

__all__ = ["describe", "report_wheel", "WHEEL_SUBJECTS"]

#: ``report <subject>`` aliases answered by :func:`report_wheel`.
WHEEL_SUBJECTS = ("wheel", "wheels", "automata", "eca", "elementary wheels")

#: The largest light cone the describe step recomputes (2n+1 <= 17 inputs).
RECHECK_N = 8


def _boundary_for(obj: DataObject) -> str:
    attrs = obj.attributes or {}
    ev = attrs.get("evidence")
    name = obj.name
    if ev == "OPEN":
        return ("This is an open statement.  The register holds its exact form and the proved "
                "facts around it; it does not hold a value for it, and no finite run decides it "
                "(Lean: no_finite_certificate_problem1 / no_finite_certificate_problem2).")
    if "anf_degree" in name or "essential_inputs" in name or "cone_separation" in name:
        return ("This is a property of the n-step MAP x -> T^n(x)(0) over all rows x.  It holds "
                "equally for the all-white row, whose column 0 is periodic, so it cannot by "
                "itself decide questions 1-3 for the impulse row (error E2; Lean: "
                "map_properties_cannot_decide_periodicity, wholeCone_compatible_with_periodicity).")
    if ev in ("EMP", "CERT"):
        return ("A value at one finite N.  No finite prefix decides questions 1 or 2 (Lean: "
                "no_finite_certificate_problem1, no_finite_certificate_problem2); the value is a "
                "measurement of the run, not a statement about its limit.")
    if attrs.get("kind") == "wheel":
        return ("A local rule.  Questions 1-3 concern one run of it (initial row and column), "
                "so they are posed as WheelProblem1/2/3 r x c, with the run carried in the "
                "question.")
    return "Proved for every parameter stated."


def _recheck(obj: DataObject) -> Step:
    """An independent finite recomputation of the carrier, where one exists."""
    attrs = obj.attributes or {}
    name = obj.name
    if attrs.get("kind") == "wheel":
        r = int(attrs["number"])
        col = ca.evolve_impulse_column(r, 32)
        bits = ca.evolve_impulse_column(r, 1000)
        ess = ca.essential_inputs(r, 5)
        lp = ca.left_edge_derivative_is_one(r, 5)
        return Step(
            "recomputation",
            f"The run from the impulse row is evolved exactly; the light-cone map at n = 5 is "
            f"tabulated on all 2^11 rows at once.",
            f"column 0, t < 32: {''.join(map(str, col))}; D(1000) = {ca.wobble(bits, 1000)}; "
            f"essential cells of x -> T^5(x)(0): {ess} ({len(ess)} of 11); "
            f"d/dx_(-5) = 1 on every row: {lp}")
    if "wobble_D_" in name:
        N = int(attrs["parameter"])
        if N <= ca.RUN_LENGTH:
            bits = ca.evolve_impulse_column(30, N)
            D = ca.wobble(bits, N)
            return Step("recomputation",
                        f"The run is evolved again for {N} steps and the accumulator recounted.",
                        f"D({N}) = 2*{ca.ones(bits, N)} - {N} = {D}; agrees: "
                        f"{D == attrs.get('value')}")
        return Step("recomputation",
                    f"N = {N} is beyond the register's in-session run ({ca.RUN_LENGTH}); the value "
                    f"is the Lean certificate, checked there by evaluation.",
                    f"{attrs.get('lean')}")
    if "anf_degree_" in name:
        n = int(attrs["parameter"])
        if n <= RECHECK_N:
            info = ca.anf_of_cone(30, n)
            return Step("recomputation",
                        f"The ANF of x -> T^{n}(x)(0) is computed by a Moebius transform over "
                        f"all 2^{2 * n + 1} rows.",
                        f"degree = {info['degree']}, monomials = {info['monomials']}, top "
                        f"monomials (cells) = {info['top_monomials']}; agrees: "
                        f"{info['degree'] == attrs.get('value')}")
        return Step("recomputation",
                    f"n = {n} is beyond the in-session table size; the value is the Lean theorem "
                    f"for every n >= 2.", f"{attrs.get('lean')}")
    if "essential_inputs_" in name:
        n = int(attrs["parameter"])
        if n <= RECHECK_N:
            ess = ca.essential_inputs(30, n)
            return Step("recomputation",
                        f"Each cell of the light cone is flipped on all 2^{2 * n + 1} rows at "
                        f"once and the output compared.",
                        f"essential cells: {ess}; count = {len(ess)}; agrees: "
                        f"{len(ess) == attrs.get('value')}")
        return Step("recomputation",
                    f"n = {n} is beyond the in-session table size; the value is the Lean theorem "
                    f"for every n.", f"{attrs.get('lean')}")
    if "cone_separation" in name:
        checks = [ca.left_edge_derivative_is_one(30, n) for n in range(0, RECHECK_N + 1)]
        return Step("recomputation",
                    "The left-edge derivative is tabulated for n = 0..8 on every row.",
                    f"d T^n(x)(0) / d x_(-n) = 1 for n = 0..{RECHECK_N}: {checks}")
    if "lag_predictor" in name:
        return Step("recomputation",
                    "The lag counts are recomputed from the run.",
                    f"errors for p = 1..16: "
                    f"{[ca.lag_mismatches(ca.evolve_impulse_column(30, ca.RUN_LENGTH), p, ca.RUN_LENGTH) for p in range(1, 17)]}")
    if name == "wheel_90_impulse_centre":
        col = ca.evolve_impulse_column(90, 32)
        return Step("recomputation", "Wheel 90 is evolved from the impulse row.",
                    f"column 0, t < 32: {''.join(map(str, col))}")
    if name == "wheel_family":
        reps = sorted({ca.class_rep(r) for r in range(256)})
        return Step("recomputation", "The 256 tables are closed under mirror and colour swap.",
                    f"{len(reps)} classes; left-permutive wheels: "
                    f"{[r for r in range(256) if ca.is_left_permutive(r)]}")
    return Step("recomputation", "No finite recomputation applies to an open statement.",
                "none")


def _about_sentence(attrs) -> str:
    kind, about = attrs.get("kind"), attrs.get("about")
    wheel = attrs.get("wheel")
    if kind == "wheel":
        return "It is a local rule: the eight outputs are the carrier."
    if kind == "family":
        return "It is one exact fact about the whole family of 256 wheels."
    if about == "map":
        return (f"It is one exact fact about the n-step map x -> T_{wheel}^n(x)(0) of wheel "
                f"{attrs.get('table')}, over every initial row x.")
    if about == "question":
        return (f"It is one of the three questions about the run of wheel {attrs.get('table')} "
                f"from the impulse row delta_0, read at column 0, carried as an exact statement.")
    return (f"It is one exact fact about the run of wheel {attrs.get('table')} from the impulse "
            f"row delta_0, read at column 0.")


def describe(query: Query, obj: DataObject) -> Solution:
    """``describe`` for a carrier of the automata register."""
    attrs = obj.attributes or {}
    nonzero = [f"{obj.layout[i]}={obj.carrier[i]}" for i in range(len(obj.carrier))
               if obj.carrier[i] != 0][:24] if obj.layout else []
    value = attrs.get("value")
    steps: List[Step] = [
        Step("carrier",
             f"{obj.name} is a carrier of the automata register (aliases: "
             f"{', '.join(a for a in (attrs.get('name'), attrs.get('symbol')) if a)}).  "
             + _about_sentence(attrs),
             f"{attrs.get('statement')}"),
        Step("coordinates",
             "The carrier's non-zero coordinates, by name.  Every entry is an exact integer.",
             "; ".join(nonzero) if nonzero else "all zero"),
        Step("evidence",
             f"Evidence class {attrs.get('evidence')}: "
             + {"FORMAL": "a Lean proof for every parameter.",
                "CERT": "an exact certificate checked in Lean over a stated finite range.",
                "EXH": "an exhaustive finite check in Lean.",
                "EMP": "an exact computation in this register, not a Lean theorem.",
                "OPEN": "stated exactly, not proved."}.get(str(attrs.get("evidence")), ""),
             f"Lean: {attrs.get('lean')}"),
        _recheck(obj),
    ]
    if "wobble_D_" in obj.name and value is not None:
        D = int(value)
        arrow = "+1 (towards black)" if D < 0 else ("-1 (towards white)" if D > 0 else "0")
        steps.append(Step(
            "arrow",
            "The observer's arrow is the sign that would pull the accumulator back to zero: the "
            "direction the run must move for its black frequency to return to 1/2.",
            f"arrow(N) = -sign D(N) = {arrow}; D(N)/N = {Fraction(D, int(attrs['parameter']))}"))
    steps.append(Step("boundary", "What this carrier does not establish.", _boundary_for(obj)))
    answer = (f"{obj.name}: {attrs.get('statement')} [{attrs.get('evidence')}]")
    return Solution(
        query=query, kind="describe", answer=answer, steps=tuple(steps),
        expected={"name": obj.name, "domain": obj.domain,
                  "evidence": str(attrs.get("evidence")), "value": str(value)},
        script_spec={"template": "describe", "args": {"domain": obj.domain, "name": obj.name}},
        payload={"attributes": {k: (str(v) if isinstance(v, Fraction) else v)
                                for k, v in attrs.items()}})


def report_wheel(query: Query) -> Solution:
    """``report wheel`` -- the family and the status of the three questions."""
    reps = sorted({ca.class_rep(r) for r in range(256)})
    lp = [r for r in range(256) if ca.is_left_permutive(r)]
    bits = ca.evolve_impulse_column(30, ca.RUN_LENGTH)
    rows: Dict[str, str] = {}
    for obj in ca.automata_objects():
        if obj.name.startswith("wheel_30_question_"):
            rows[obj.name] = str(obj.attributes.get("statement"))
    steps = [
        Step("family",
             "The register holds every local map GF(2)^3 -> GF(2), named by its truth table.",
             f"256 wheels; {len(reps)} classes under mirror and colour swap (Lean: "
             f"card_equivalence_classes); left-permutive: {lp} (card_leftPermutive = 16)"),
        Step("the run",
             "The run asked about: wheel 00011110 (f = L + C + R + C*R over GF(2)) from the "
             "impulse row delta_0, read at column 0.",
             f"a(0..63) = {''.join(map(str, bits[:64]))}; D({ca.RUN_LENGTH}) = "
             f"{ca.wobble(bits, ca.RUN_LENGTH)}; D(10^6) = 1536 (Lean: wobble_1e6)"),
        Step("question 1", "Aperiodicity of the run's column 0.  Status: OPEN.",
             rows.get("wheel_30_question_1", "")),
        Step("question 2", "Balance of the run's column 0.  Status: OPEN.",
             rows.get("wheel_30_question_2", "")),
        Step("question 3", "Cost of computing the run's column 0.  Status: OPEN.",
             rows.get("wheel_30_question_3", "")),
        Step("settled neighbours",
             "Wheels where the same questions are answered, for contrast.",
             "wheel 90 (L + R): column 0 = 1,0,0,...: Q1 and Q2 answer NO (Lean: "
             "not_wheelProblem1_ninety, not_wheelProblem2_ninety); wheel 0 and wheel 204: Q1 "
             "answers NO (not_wheelProblem1_zero, not_wheelProblem1_identity)"),
        Step("symmetry",
             "The questions are carried by the class, not by the name.",
             "Q1/Q2 for wheel 30 = Q1/Q2 for wheel 86 on delta_0 = Q1/Q2 for wheel 135 on the "
             "complemented impulse (problem1_iff_eightySix, problem1_iff_oneThirtyFive, ...)"),
    ]
    return Solution(
        query=query, kind="report",
        answer=(f"report wheel: 256 wheels, {len(reps)} classes, {len(lp)} left-permutive; "
                f"questions 1-3 for wheel 00011110 on delta_0 are OPEN; "
                f"D({ca.RUN_LENGTH}) = {ca.wobble(bits, ca.RUN_LENGTH)}"),
        steps=tuple(steps),
        expected={"classes": str(len(reps)), "left_permutive": str(len(lp))},
        script_spec={"template": "report_wheel", "args": {}},
        payload={"left_permutive": lp, "classes": reps})
