"""``glm_universal.runtime.wheel_report`` -- answers about the automata register ("the Wheel").

Two entry points, both called from :class:`~glm_universal.runtime.session.GeometricSession`:

* :func:`describe` -- ``describe <automata carrier>``: the carrier's exact statement, its
  evidence class and Lean reference, an independent recomputation where one is finite, and
  the boundary of what the carrier establishes.
* :func:`report_wheel` -- ``report wheel``: the family census and the status of the three
  questions for wheel ``00011110`` from the impulse row.  Round 10 adds four more subjects:
  ``report wheel steps`` (the run step by step at the centre), ``report wheel induction``
  (the wheel induced from rows of the diagram, ARC-style), ``report wheel observer`` (what one
  column can tell) and ``report wheel perspective`` (how the arrow changes with the frame).

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
WHEEL_SUBJECTS = ("wheel", "wheels", "automata", "eca", "elementary wheels",
                  # Round 10
                  "wheel steps", "wheel step", "wheel induction", "wheel observer",
                  "wheel observers", "wheel perspective")

#: The largest light cone the describe step recomputes (2n+1 <= 17 inputs).
RECHECK_N = 8


def _boundary_for(obj: DataObject) -> str:
    attrs = obj.attributes or {}
    ev = attrs.get("evidence")
    name = obj.name
    k10 = attrs.get("kind_r10")
    if k10 == "step":
        return ("One step of one finite run.  The step law holds at every t, but a step, or any "
                "finite number of them, says nothing about the limit questions 1 and 2 (Lean: "
                "no_finite_certificate_problem1, no_finite_certificate_problem2).")
    if k10 in ("induction", "observer"):
        return ("This says which wheel produced the data, not how that wheel's run behaves in "
                "the limit.  Identifying the rule is a fact about the 256 tables; questions "
                "1-3 stay OPEN for wheel 30 (and the same for 86, which the centre cannot tell "
                "apart from it).")
    if k10 == "arrow":
        return ("This says how the arrow transforms under a change of frame, for every N.  It "
                "does not say what sign the arrow takes in the long run, nor whether D(N)/N -> 0 "
                "(question 2, OPEN).")
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


def _complement_impulse_column(r: int, steps: int) -> List[int]:
    """Column 0 of wheel ``r`` from the complemented impulse (all black, one white cell),
    evolved on a window with the black background carried explicitly."""
    h = steps + 2
    row = [0 if c == 0 else 1 for c in range(-h, h + 1)]
    bg, out = 1, []
    for _ in range(steps):
        out.append(row[h])
        padded = [bg] + row + [bg]
        row = [ca.local_rule(r, padded[i - 1], padded[i], padded[i + 1])
               for i in range(1, len(padded) - 1)]
        bg = ca.local_rule(r, bg, bg, bg)
    return out


def _recheck_round10(obj: DataObject):
    attrs = obj.attributes or {}
    k10 = attrs.get("kind_r10")
    if k10 == "step":
        t = int(attrs["parameter"])
        rows = ca.impulse_rows(30, t + 1)
        h = t + 2
        L, C, R = rows[t][h - 1], rows[t][h], rows[t][h + 1]
        a_next = rows[t + 1][h]
        return Step("recomputation",
                    f"Rows {t} and {t + 1} are evolved again from the impulse and the centre cell "
                    f"is read off; the local rule is applied to the centre neighbourhood by hand.",
                    f"(L,C,R) = ({L},{C},{R}); f = L + C + R + C*R = {(L + C + R + C * R) % 2}; "
                    f"evolved a({t + 1}) = {a_next}; agrees: {a_next == attrs.get('value')}")
    if k10 == "induction":
        from ..reasoning import wheel_induction as wi
        T = int(attrs["parameter"])
        pairs, q, true = wi.rule30_demonstrations(T)
        res = wi.induce_rows(pairs, q)
        verdict = (f"answered {res['answer']} (true row {''.join(map(str, true))})"
                   if res["status"] == "answered" else
                   f"refused: {[''.join(map(str, n)) for n in res['missing']]} unseen; "
                   f"candidates {res.get('answers')}")
        return Step("recomputation",
                    f"The induction is re-run: every one of the 256 tables is tried against the "
                    f"{T} demonstrations, then asked for row {T + 1}.",
                    f"survivors {res['survivors'] if len(res['survivors']) <= 8 else len(res['survivors'])}; "
                    f"{verdict}; survivors = 2^(#unseen): "
                    f"{len(res['survivors']) == 2 ** len(res['unseen'])}")
    if k10 == "observer":
        from ..reasoning import wheel_induction as wi
        c = int(attrs["parameter"])
        K = int(attrs["value"])
        bits = ca.evolve_impulse_column(30, K, c)
        now = wi.induce_column(bits, c)["survivors"]
        before = wi.induce_column(bits[:K - 1], c)["survivors"]
        return Step("recomputation",
                    f"All 256 wheels are evolved from the impulse and read at column {c}, with "
                    f"{K} and with {K - 1} values.",
                    f"{K} values: survivors {now}; {K - 1} values: "
                    f"{before if len(before) <= 8 else str(len(before)) + ' survivors'}")
    if k10 == "arrow":
        N = 400
        a30 = ca.evolve_impulse_column(30, N)
        if "mirror" in obj.name:
            other = ca.evolve_impulse_column(86, N)
            ok = all(ca.wobble(other, n) == ca.wobble(a30, n) for n in range(N + 1))
            return Step("recomputation",
                        f"Wheel 86 is evolved from the impulse and its accumulator compared with "
                        f"wheel 30's for every N <= {N}.",
                        f"D_86(N) = D_30(N) for all N <= {N}: {ok}; D({N}) = {ca.wobble(a30, N)}")
        other = _complement_impulse_column(135, N)
        ok = all(ca.wobble(other, n) == -ca.wobble(a30, n) for n in range(N + 1))
        return Step("recomputation",
                    f"Wheel 135 is evolved from the complemented impulse (black background "
                    f"carried exactly) and its accumulator compared for every N <= {N}.",
                    f"D_135(N) = -D_30(N) for all N <= {N}: {ok}; D_30({N}) = "
                    f"{ca.wobble(a30, N)}, D_135({N}) = {ca.wobble(other, N)}")
    return None


def _recheck(obj: DataObject) -> Step:
    """An independent finite recomputation of the carrier, where one exists."""
    attrs = obj.attributes or {}
    name = obj.name
    r10 = _recheck_round10(obj)
    if r10 is not None:
        return r10
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
    k10 = attrs.get("kind_r10")
    if k10 == "step":
        return "It is one step of the run at the centre: the neighbourhood read, the rule applied."
    if k10 == "induction":
        return ("It is the ARC-style reading: which wheels reproduce rows of the diagram, and "
                "whether the next row follows.")
    if k10 == "observer":
        return "It is what an observer standing at one column can tell about the wheel."
    if k10 == "arrow":
        return "It is how the observer's arrow changes when the frame of view is changed."
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
    if attrs.get("kind_r10") == "step":
        D = int(attrs["D_next"])
        t1 = int(attrs["parameter"]) + 1
        arrow = "+1 (towards black)" if D < 0 else ("-1 (towards white)" if D > 0 else "0")
        steps.append(Step(
            "arrow",
            "After this step the observer's arrow points the way that would bring the "
            "accumulator back to zero.",
            f"D({t1}) = {D}; arrow({t1}) = -sign D = {arrow}"))
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
    subject = str((query.options or {}).get("subject", "")).strip().lower()
    if subject in ("wheel steps", "wheel step"):
        return report_steps(query)
    if subject == "wheel induction":
        return report_induction(query)
    if subject in ("wheel observer", "wheel observers"):
        return report_observer(query)
    if subject == "wheel perspective":
        return report_perspective(query)
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


# ===========================================================================
# Round 10: the run step by step, the wheel induced, the observer, the frame
# ===========================================================================

def _solution(query: Query, answer: str, steps: List[Step], template: str,
              payload: Dict[str, object]) -> Solution:
    return Solution(query=query, kind="report", answer=answer, steps=tuple(steps),
                    expected={"subject": template}, script_spec={"template": template, "args": {}},
                    payload=payload)


def report_steps(query: Query, count: int = 16) -> Solution:
    """``report wheel steps``: the first steps of the run at the centre, one row per step."""
    bits = ca.evolve_impulse_column(30, count + 1)
    rows = ca.impulse_rows(30, count)
    h = count + 1
    steps: List[Step] = [Step(
        "the step law",
        "Each new centre cell is the rule applied to the three cells above it: left, centre, "
        "right.  Over GF(2) the rule of wheel 00011110 is f = L + C + R + C*R.",
        "a(t+1) = f(x_t(-1), a(t), x_t(1));  D(N) = 2*#{i < N : a(i) = 1} - N, so "
        "D(t+1) = D(t) + (2 a(t) - 1)  (Lean: ecaEvolve_succ, ecaRule_30, wobble_succ)")]
    table = []
    for t in range(count):
        L, C, R = rows[t][h - 1], rows[t][h], rows[t][h + 1]
        a1 = ca.local_rule(30, L, C, R)
        assert a1 == bits[t + 1]
        D = ca.wobble(bits, t + 1)
        arrow = 0 if D == 0 else (-1 if D > 0 else 1)
        table.append(f"t={t}: ({L},{C},{R}) -> a({t + 1})={a1}, D({t + 1})={D}, "
                     f"arrow={arrow:+d}")
    steps.append(Step("steps", f"The first {count} steps at the centre, each recomputed.",
                      "; ".join(table)))
    nb_counts: Dict[str, int] = {}
    long_rows = ca.impulse_rows(30, 1000)
    H = 1001
    for t in range(1000):
        key = "".join(map(str, (long_rows[t][H - 1], long_rows[t][H], long_rows[t][H + 1])))
        nb_counts[key] = nb_counts.get(key, 0) + 1
    steps.append(Step(
        "neighbourhoods at the centre",
        "How often each neighbourhood occurs above the centre cell in the first 1000 steps "
        "(an exact count, not a theorem).",
        ", ".join(f"{k}: {nb_counts.get(k, 0)}" for k in
                  ("000", "001", "010", "011", "100", "101", "110", "111"))))
    steps.append(Step(
        "boundary", "What the steps do not establish.",
        "Every step is exact, and the step law holds for every t, but no finite number of steps "
        "decides questions 1 or 2 (no_finite_certificate_problem1/2)."))
    return _solution(query, f"report wheel steps: the first {count} steps of wheel 00011110 at "
                     f"the centre; D({count}) = {ca.wobble(bits, count)}", steps,
                     "report_wheel_steps", {"count": count})


def report_induction(query: Query) -> Solution:
    """``report wheel induction``: the wheel induced from rows of the diagram."""
    from ..reasoning import wheel_induction as wi
    steps: List[Step] = []
    # the GLM's existing induction families, on the same task
    try:
        from ..reasoning import pipeline_kit as pk
        pairs, q, _true = wi.rule30_demonstrations(3)
        res = pk.solve([((a,), (b,)) for a, b in pairs], (q,))
        steps.append(Step(
            "existing families",
            "The GLM's induction solver (pipeline kit: permutations, XOR masks, shifts and their "
            "compositions) on rows 0..3 of the run.",
            f"status {res['status']}; {'; '.join(res['steps'])}"))
    except Exception as error:  # pragma: no cover -- reported, not hidden
        steps.append(Step("existing families", "The pipeline kit could not be run here.",
                          f"{type(error).__name__}: {error}"))
    lines = []
    for T in ca.INDUCTION_ROWS:
        pairs, q, true = wi.rule30_demonstrations(T)
        res = wi.induce_rows(pairs, q)
        surv = res["survivors"]
        lines.append(
            f"rows 0..{T}: {len(surv)} survivor(s){' ' + str(surv) if len(surv) <= 4 else ''}, "
            f"unseen {[''.join(map(str, n)) for n in res['unseen']] or 'none'}, row {T + 1} "
            + (f"answered ({res['answer'] == ''.join(map(str, true))} against the true row)"
               if res["status"] == "answered" else "refused"))
    steps.append(Step(
        "the wheel family",
        "The radius-1 family: every one of the 256 tables is tried; the reading answers only when "
        "every survivor gives the same next row.",
        "; ".join(lines)))
    steps.append(Step(
        "why the refusals are exact",
        "A wheel fits the rows iff it agrees on the neighbourhoods they show; the next row "
        "follows iff each of its neighbourhoods was shown.  So refusing exactly when the "
        "survivors disagree is refusing exactly when the query needs an unseen neighbourhood.",
        "Lean: rows_agree_iff, next_row_determined_iff (WheelInduction.lean); rows_identify_thirty "
        "(rows 0..4 determine 30), rows_three_do_not_identify and row_four_not_determined "
        "(wheel 62 shares rows 0..3, differs at 101)"))
    steps.append(Step("boundary", "What this does not establish.",
                      "Identifying the rule from its rows is a fact about the 256 tables; it says "
                      "nothing about questions 1-3 for the run."))
    return _solution(query, "report wheel induction: rows 0..4 of the impulse run determine wheel "
                     "00011110 among all 256; rows 0..3 leave {30, 62}; the existing induction "
                     "families do not fit", steps, "report_wheel_induction", {})


def report_observer(query: Query) -> Solution:
    """``report wheel observer``: what a single column can tell about the wheel."""
    objs = {o.name: o for o in ca.automata_objects()}
    lines = []
    for c in ca.OBSERVER_COLUMNS:
        o = objs[f"wheel_30_observer_column_{ca.column_token(c)}"]
        surv = o.attributes["survivors"]
        lines.append(f"c={c}: {o.attributes['value']} values -> {surv}")
    steps = [
        Step("columns",
             "For each column c, the least number of values (from t = 0) after which the column "
             "of the impulse run leaves only wheel 30, or, at the centre, only its class.",
             "; ".join(lines)),
        Step("the centre",
             "The centre column cannot separate wheel 30 from its mirror image 86, however long "
             "it is watched.  So nothing computed from the centre column alone (its frequency, "
             "its wobble D(N), any finite-state observer) can tell which way the run is "
             "oriented.",
             "Lean: centre_column_class : ecaColumn r seed 0 = centerCol <-> r = 30 or r = 86 "
             "(r < 256); centre_prefix_class (7 values); centre_six_not_enough"),
        Step("off the centre",
             "One cell to either side, the column determines the wheel.",
             "Lean: column_one_identifies (8 values, column_one_seven_not_enough); "
             "offCentre_column_identifies (every 1 <= |c| <= 5)"),
        Step("boundary", "What this does not establish.",
             "Which wheel produced a column is a fact about the 256 tables.  Questions 1-3 are "
             "about the centre column of 30 (= that of 86), and stay OPEN."),
    ]
    return _solution(query, "report wheel observer: the centre column gives the class {30, 86} "
                     "and never less; every column with 1 <= |c| <= 5 gives wheel 30", steps,
                     "report_wheel_observer", {})


def report_perspective(query: Query) -> Solution:
    """``report wheel perspective``: the arrow -sign D(N) under the three changes of frame."""
    N_values = (10, 100, 1000)
    a30 = ca.evolve_impulse_column(30, 1000)
    a86 = ca.evolve_impulse_column(86, 1000)
    a135 = _complement_impulse_column(135, 1000)
    rows = []
    for N in N_values:
        rows.append(f"N={N}: D_30={ca.wobble(a30, N)}, D_86={ca.wobble(a86, N)}, "
                    f"D_135(complemented)={ca.wobble(a135, N)}")
    rev = [ca.wobble(a30[:1000][::-1], k) for k in (10, 100)]
    steps = [
        Step("three frames",
             "The same run seen three ways: as it is; in a mirror (wheel 86 from the impulse); "
             "with the colours swapped (wheel 135 from the complemented impulse).",
             "; ".join(rows)),
        Step("mirror",
             "Reflecting space leaves the arrow unchanged, for every N and every wheel, row and "
             "column.  The arrow carries no left/right information.",
             "observerArrow(mirror r, x(-.), -c) = observerArrow(r, x, c)  (Lean: "
             "observerArrow_mirror, observerArrow_eightySix)"),
        Step("colour",
             "Swapping the colours reverses the arrow, for every N.  The arrow is a statement "
             "about which colour the observer calls black.",
             "observerArrow(complement r, not x, c) = -observerArrow(r, x, c)  (Lean: "
             "observerArrow_complement, observerArrow_oneThirtyFive)"),
        Step("time",
             "Reading the first N values backwards: the accumulator after k backward steps is "
             "D(N) - D(N - k).",
             f"Lean: wobble_reverse (Perspective.lean); e.g. N = 1000: backward D(10) = {rev[0]}, "
             f"D(100) = {rev[1]}"),
        Step("what the observer Y can read",
             "The colour frame is in the arrow; the spatial frame is not in the centre column at "
             "all (centre_column_class), but is read one cell off-centre "
             "(column_one_identifies).",
             "arrow: colour frame (sign flips), not spatial frame (invariant); position: spatial "
             "frame needs an off-centre column"),
        Step("boundary", "What this does not establish.",
             "How the arrow transforms, not its long-run behaviour: question 2 (D(N)/N -> 0) "
             "stays OPEN."),
    ]
    return _solution(query, "report wheel perspective: the arrow is unchanged by the mirror and "
                     "reversed by the colour swap; the centre column cannot see the mirror",
                     steps, "report_wheel_perspective", {})
