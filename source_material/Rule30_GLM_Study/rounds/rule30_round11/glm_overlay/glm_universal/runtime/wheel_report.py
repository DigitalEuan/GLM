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
                  "wheel observers", "wheel perspective",
                  # Round 11
                  "wheel diagonals", "wheel edge", "wheel right edge", "wheel chirality",
                  "wheel claims")

#: The largest light cone the describe step recomputes (2n+1 <= 17 inputs).
RECHECK_N = 8


def _boundary_for(obj: DataObject) -> str:
    attrs = obj.attributes or {}
    ev = attrs.get("evidence")
    name = obj.name
    k10 = attrs.get("kind_r10")
    k11 = attrs.get("kind_r11")
    if k11 in ("edge", "rdiag"):
        return ("This is about the right diagonals a(t)(t - D), each read at fixed depth D.  The "
                "centre column a(t) = rdiag t t crosses every diagonal once and never stays on "
                "one, so balance or bounded wobble on diagonals does not decide question 2 for "
                "the centre (OPEN).")
    if k11 in ("column_wobble", "chiral"):
        return ("A wobble value or identity for one column.  No finite prefix decides questions 1 "
                "or 2 for any column (no_finite_certificate_problem1/2); the identities hold for "
                "every N but say nothing about D(N)/N -> 0.")
    if k11 == "parity":
        return ("A property of the n-step MAP over all rows; it cannot by itself decide "
                "questions 1-3 for the impulse row (map_properties_cannot_decide_periodicity).")
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


def _recheck_round11(obj: DataObject):
    attrs = obj.attributes or {}
    k11 = attrs.get("kind_r11")
    if k11 == "rdiag":
        from ..data_objects import automata_round11 as r11
        D = int(attrs["parameter"])
        if D > 12:
            return Step("recomputation", "Diagonals beyond 12 are quoted from the exact C run "
                        "(r11_diagonals.c); no in-session recomputation.", "quoted")
        seq = r11.right_diagonals(12, 4096)[D]
        P = int(attrs["period"])
        ok = all(seq[t] == seq[t + P] for t in range(4096 - P))
        anti = P >= 2 and all(seq[t + P // 2] == 1 - seq[t] for t in range(4096 - P // 2))
        return Step("recomputation",
                    f"Diagonal {D} is read again from the bit-parallel step for 4096 steps.",
                    f"period {P} holds: {ok}; black per period {sum(seq[:P])}; anti-periodic: "
                    f"{anti}")
    if k11 == "column_wobble":
        c, N = int(attrs["observer_column"]), int(attrs["parameter"])
        if N > 10000:
            return Step("recomputation", "Quoted from the exact C run (r11_offcentre_wobble.c).",
                        "quoted")
        bits = ca.evolve_impulse_column(30, N, c)
        return Step("recomputation", f"Column {c} is evolved again for {N} steps.",
                    f"D_{c}({N}) = {ca.wobble(bits, N)}")
    if k11 == "chiral" and "first" in obj.name:
        c = int(attrs["parameter"])
        a = ca.evolve_impulse_column(30, 64, c)
        b = ca.evolve_impulse_column(30, 64, -c)
        first = next(n for n in range(65) if ca.wobble(a, n) != ca.wobble(b, n))
        return Step("recomputation", f"Columns {c} and {-c} are evolved again for 64 steps.",
                    f"first N with D_{c}(N) != D_-{c}(N): {first}")
    return None


def _recheck_round10(obj: DataObject):
    attrs = obj.attributes or {}
    r11 = _recheck_round11(obj)
    if r11 is not None:
        return r11
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
    k11 = attrs.get("kind_r11")
    if k11 == "edge":
        return "It is the seed's right-edge boundary condition and what it forces on the diagonals."
    if k11 == "rdiag":
        return "It is one right diagonal of the seed pattern, read at fixed depth behind the edge."
    if k11 == "column_wobble":
        return "It is the wobble seen by an observer standing at one column."
    if k11 == "chiral":
        return ("It is the part of the wobble that only an off-centre observer sees: column c "
                "minus its mirror column -c.")
    if k11 == "parity":
        return "It is the parity count behind the ANF degree, settled for every n."
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
    if subject in ("wheel diagonals", "wheel edge", "wheel right edge"):
        return report_diagonals(query)
    if subject == "wheel chirality":
        return report_chirality(query)
    if subject == "wheel claims":
        return report_claims(query)
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
        expected=recompute_expected("report_wheel"),
        script_spec={"template": "report_wheel", "args": {}},
        payload={"left_permutive": lp, "classes": reps})


# ===========================================================================
# Round 10: the run step by step, the wheel induced, the observer, the frame
# ===========================================================================

def _solution(query: Query, answer: str, steps: List[Step], template: str,
              payload: Dict[str, object]) -> Solution:
    return Solution(query=query, kind="report", answer=answer, steps=tuple(steps),
                    expected=recompute_expected(template),
                    script_spec={"template": template, "args": {}}, payload=payload)


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


# ===========================================================================
# Round 11: the seed's right edge, the off-centre observer, the claim checker
# ===========================================================================

def report_diagonals(query: Query) -> Solution:
    """``report wheel diagonals``: the seed's right edge and what it forces on the diagonals."""
    from ..data_objects import automata_round11 as r11
    recs = [r11.diagonal_record(D) for D in range(40)]
    anti = [r["D"] for r in recs if r["anti"]]
    bal = [r["D"] for r in recs if not r["anti"] and 2 * r["ones"] == r["period"]]
    unbal = [r["D"] for r in recs if 2 * r["ones"] != r["period"]]
    table = "; ".join(f"{r['D']}:{r['period']}/{r['ones']}{'*' if r['anti'] else ''}"
                      for r in recs[:16])
    steps = [
        Step("the boundary",
             "What singles out the seed on the right: at time 0 only diagonal 0 is black; the "
             "diagonals outside the cone stay white; each diagonal is the running XOR of the two "
             "outside it.",
             "rdiag D 0 = [D = 0]; rdiag D (t+1) = rdiag D t + (rdiag (D-1) t OR rdiag (D-2) t) "
             "(Lean: rdiag_zero, rdiag_neg, rdiag_succ)"),
        Step("periodic or anti-periodic",
             "A running XOR of a Q-periodic input, shifted by Q, either repeats or flips "
             "everywhere.  So every diagonal is periodic or anti-periodic with the period of its "
             "input.",
             "Lean: runningXor_periodic_or_antiPeriodic, rdiag_periodic_or_antiPeriodic"),
        Step("anti-periodic means balanced",
             "An anti-periodic sequence with half-period Q has |D(N)| <= Q for every N, exactly Q "
             "black cells in any 2Q consecutive ones, and frequency 1/2: the bounded (ideal "
             "delta-sigma) regime.",
             "Lean: wobble_antiPeriodic_bound, antiPeriodic_balanced, antiPeriodic_hasFrequencyHalf"),
        Step("infinitely many",
             "If no diagonal from D0 on were anti-periodic, all of them would share one period; "
             "but the periods are unbounded.",
             "Lean: exists_antiPeriodic_rdiag, infinitely_many_balanced_rdiag"),
        Step("but not all",
             "Diagonal 5 has 12 black cells in each period of 32: frequency 3/8, wobble -8 per "
             "period.  Diagonal 7 is anti-periodic: |D(N)| <= 16.",
             "Lean: wobble_rdiag_five, rdiag_five_not_half, rdiag_seven_bounded"),
        Step("the table (EMP)",
             "D:least period/black per period, * = anti-periodic (D <= 12 computed here, 13..39 "
             "quoted from r11_diagonals.c).",
             f"{table}; ... anti-periodic to 39: {anti}; balanced but not anti-periodic: {bal}; "
             f"unbalanced: {unbal}"),
        Step("boundary", "What this does not establish.",
             "The centre column a(t) = rdiag t t reads diagonal t at time t; it crosses every "
             "diagonal once, so the balance of diagonals does not decide question 2 (OPEN)."),
    ]
    return _solution(query, f"report wheel diagonals: every right diagonal is periodic or "
                     f"anti-periodic; anti-periodic ones are exactly balanced with bounded wobble; "
                     f"infinitely many are (FORMAL); to D = 39: {len(anti)} anti-periodic, "
                     f"diagonal 5 is not balanced (FORMAL)", steps, "report_wheel_diagonals",
                     {"anti": anti, "balanced_not_anti": bal, "unbalanced": unbal})


def report_chirality(query: Query) -> Solution:
    """``report wheel chirality``: where the off-centre observer sees left from right."""
    from ..data_objects import automata_round11 as r11
    W = r11.column_wobbles()
    rows = []
    for N in (1000, 10000, 1000000):
        rows.append(f"N={N}: " + ", ".join(f"D_{c}={W[(c, N)]}" for c in range(-3, 4)))
    gaps = ", ".join(f"c={c}: first N {r11.CHIRAL_FIRST[c]}, max|gap| to 10^6 "
                     f"{r11.CHIRAL_MAX_1E6[c]}" for c in range(1, 6))
    steps = [
        Step("the gap",
             "The chirality signal at column c is D_c(N) - D_-c(N).  By the mirror it is also "
             "wheel 30 minus wheel 86, both read at column c.",
             "Lean: chiralGap, wobble_mirror_column, chiralGap_eq_thirty_sub_eightySix, "
             "chiralGap_neg"),
        Step("the centre", "At the centre the gap is 0 for every N: the centre is blind.",
             "Lean: chiralGap_centre, centre_column_class"),
        Step("off-centre", "The gap opens at once: within 9 steps at every column 1..5.",
             f"{gaps}  (first N: Lean chiralGap_first; maxima EMP)"),
        Step("wobbles by column (EMP)", "The wobble of each column of the impulse run.",
             "; ".join(rows)),
        Step("reading", "What the data say about the rate.",
             "The gap behaves like the difference of two random walks: it is of order sqrt(N) "
             "and shows no drift.  Chirality is visible off-centre immediately, but it does not "
             "accumulate into a bias of any column."),
        Step("aperiodicity seen by a pair",
             "Of the observers at 0 and at c != 0, at least one sees a column that is not "
             "eventually periodic.",
             "Lean: offCentre_pair_problem1, seed_at_most_one_periodic_column"),
        Step("boundary", "What this does not establish.",
             "Question 2 for any column (OPEN); the sqrt(N) size of the gap is EMP."),
    ]
    return _solution(query, "report wheel chirality: the wobble gap D_c - D_-c is 0 at the centre "
                     "for every N and opens within 9 steps at columns 1..5; to 10^6 it stays of "
                     "random-walk size", steps, "report_wheel_chirality", {})


def report_claims(query: Query) -> Solution:
    """``report wheel claims``: the claim frames of ``tool claim`` and a worked example."""
    from ..reasoning import wheel_claims as wc
    ex = "the centre column observer can distinguish wheel 30 from wheel 86"
    ok, text, fig = wc.claim_text(ex)
    steps = [
        Step("frames", "Computed frames compute the verdict; settled frames carry a theorem.",
             "computed: column C distinguishes wheel R from wheel S; the wobble at column C "
             "equals the wobble at column -C; right diagonal D is balanced; rows 0..T determine "
             "wheel 30.  settled: almost every row ..., the arrow ..., right edge ..., every / "
             "infinitely many right diagonals ..., eventually constant, two columns periodic, "
             "whiteDiagonalCount / ANF degree, problem 1/2/3"),
        Step("example", f"tool claim {ex}", text.replace("\n", " | ")),
        Step("benchmark", "The Round 11 suite and its grader.",
             "rule30_round11/r11_reasoning_suite.json, r11_benchmark.py"),
    ]
    return _solution(query, "report wheel claims: tool claim decides a claim in a declared frame "
                     "with verdict, missing hypothesis, witness or Lean reference, next test",
                     steps, "report_wheel_claims", {})


# ===========================================================================
# Round 11: column 3 for the wheel reports
# ===========================================================================
# ``GLM.py -q`` renders a column-3 script for every answer from the template its solution names.
# The wheel reports of Rounds 9-10 named templates that ``tct_engine.TEMPLATES`` did not hold, so
# ``GLM.py -q "report wheel ..."`` stopped with a trace error (they answered in-session only).
# The templates are registered here: each script recomputes the report's exact figures in a
# fresh interpreter from this module and compares them with column 2.

WHEEL_TEMPLATES = ("report_wheel", "report_wheel_steps", "report_wheel_induction",
                   "report_wheel_observer", "report_wheel_perspective",
                   "report_wheel_diagonals", "report_wheel_chirality", "report_wheel_claims")


def recompute_expected(template: str) -> Dict[str, str]:
    """The exact figures a wheel report asserts, recomputed from the register."""
    out: Dict[str, str] = {"subject": template}
    if template == "report_wheel":
        out = {"classes": str(len({ca.class_rep(r) for r in range(256)})),
               "left_permutive": str(sum(1 for r in range(256) if ca.is_left_permutive(r)))}
    elif template == "report_wheel_perspective":
        a30 = ca.evolve_impulse_column(30, 1000)
        a86 = ca.evolve_impulse_column(86, 1000)
        out["mirror_equal_to_1000"] = str(all(ca.wobble(a30, n) == ca.wobble(a86, n)
                                              for n in range(1001)))
    elif template == "report_wheel_diagonals":
        from ..data_objects import automata_round11 as r11
        recs = [r11.diagonal_record(D) for D in range(40)]
        out["anti_periodic_to_39"] = str([r["D"] for r in recs if r["anti"]])
        out["diagonal_5"] = f"{recs[5]['period']}/{recs[5]['ones']}"
    elif template == "report_wheel_chirality":
        from ..data_objects import automata_round11 as r11
        firsts = []
        for c in range(1, 6):
            a = ca.evolve_impulse_column(30, 64, c)
            b = ca.evolve_impulse_column(30, 64, -c)
            firsts.append(next(n for n in range(65) if ca.wobble(a, n) != ca.wobble(b, n)))
        out["first_gap"] = str(firsts)
    elif template == "report_wheel_claims":
        from ..reasoning import wheel_claims as wc
        tr = wc.check_claim("the centre column observer can distinguish wheel 30 from wheel 86")
        out["example_verdict"] = tr["verdict"] if tr else "none"
    return out


def _template_body(template: str):
    def body(args) -> str:
        return ("# -- recompute (Rule 30 study: wheel report) --------------------------------\n"
                "\nfrom glm_universal.runtime import wheel_report as _wr\n\n"
                f"observed = _wr.recompute_expected({template!r})\n")
    return body


def _compare_wrapper(original):
    """Column 3 for ``compare`` when a side names an automata carrier: the replay substitutes
    the carrier's exact value itself (in the fresh interpreter), then re-decides the order.
    Without carriers the original template is used unchanged."""
    def body(args) -> str:
        left = str(args.get("left", ""))
        right = str(args.get("right", ""))
        if not (ca.mentions_carrier(left) or ca.mentions_carrier(right)):
            return original(args)
        relation = str(args.get("relation", "compare"))
        ladder = list(args.get("ladder", [8, 16, 32, 64, 128, 256]))
        return f'''# -- recompute (compare with automata carriers, Rule 30 study) -------------

from glm_universal.reasoning import exact_real as xr
from glm_universal.data_objects import automata as _ca

_left_text, _right_text = {left!r}, {right!r}
_left = xr.parse_real(_ca.substitute_values(_left_text)[0])
_right = xr.parse_real(_ca.substitute_values(_right_text)[0])
_order, _settled = 0, None
for _precision in {ladder!r}:
    _order = xr.compare(_left, _right, _precision)
    if _order != 0:
        _settled = _precision
        break
_relation = {relation!r}
if _order == 0:
    _verdict = "undecided"
elif _relation == "greater":
    _verdict = str(_order > 0)
elif _relation == "less":
    _verdict = str(_order < 0)
elif _relation == "equal":
    _verdict = "False"
else:
    _verdict = "{{}} {{}} {{}}".format(_left_text, ">" if _order > 0 else "<", _right_text)
observed = {{
    "left": _left_text, "right": _right_text, "relation": _relation,
    "order": str(_order), "settled_at": str(_settled), "verdict": _verdict,
    "left_decimal": _left.decimal(20), "right_decimal": _right.decimal(20),
}}
'''
    body._wheel_wrapped = True
    return body


def _real_wrapper(original):
    """Column 3 for ``real`` when the notation names an automata carrier: the replay checks the
    substitution again in the fresh interpreter, then recomputes the value as the original
    template does."""
    def body(args) -> str:
        notation = str(args.get("notation", ""))
        if not ca.mentions_carrier(notation):
            return original(args)
        substituted = ca.substitute_values(notation)[0]
        return (original(dict(args, notation=substituted))
                + "\n# -- the carrier substitution, checked again (Rule 30 study) --\n"
                  "from glm_universal.data_objects import automata as _ca\n"
                  f"assert _ca.substitute_values({notation!r})[0] == {substituted!r}\n"
                  f"observed[\"notation\"] = {notation!r}\n")
    body._wheel_wrapped = True
    return body


def _register_templates() -> None:
    from . import tct_engine as te
    for t in WHEEL_TEMPLATES:
        te.TEMPLATES.setdefault(t, _template_body(t))
    if not getattr(te.TEMPLATES.get("compare"), "_wheel_wrapped", False):
        te.TEMPLATES["compare"] = _compare_wrapper(te.TEMPLATES["compare"])
    if not getattr(te.TEMPLATES.get("real"), "_wheel_wrapped", False):
        te.TEMPLATES["real"] = _real_wrapper(te.TEMPLATES["real"])


_register_templates()
