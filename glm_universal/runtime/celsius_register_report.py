"""``glm_universal.runtime.celsius_register_report`` -- the measurement of
the Celsius-register round.

``studies/CELSIUS_REGISTER_STUDY.md`` (Phase 99) declares eight marks over the
corpus of :mod:`glm_universal.evaluation.celsius_register_cases`; this module
takes the seven that are measured (the eighth is the Lean file,
``RequestProject/GLM/CelsiusRegister.lean``).  The register itself is
:mod:`glm_universal.data_objects.fixed_points`, the offset row is
``fixed_point:temperature_C`` of
:mod:`glm_universal.reasoning.scale_conversion`, and the planner reads it
through :func:`glm_universal.runtime.quantity_units.scale_into_si_affine`.

Two controls: **offset dropped**
(:data:`glm_universal.reasoning.scale_conversion.OFFSETS` off -- a Celsius
reading taken as kelvins) and **register absent**
(:data:`glm_universal.data_objects.fixed_points.ACTIVE` off, on a fresh
session -- the machine before the round).
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from . import router
from . import stepwise as sw
from ..data_objects import fixed_points as fp
from ..reasoning import scale_conversion as sc
from ..reasoning import stepwise_script as ss

__all__ = ["switched", "register_report", "order_report", "column_report",
           "planner_report", "control_report", "earlier_report",
           "scripts_report", "agreement_report", "celsius_register_report"]


class switched:
    """``with switched(OFFSETS=False): ...`` or ``ACTIVE=False``: set a
    switch of the round for a control, and restore it after."""

    _HOMES = {"OFFSETS": sc, "ACTIVE": fp}

    def __init__(self, **flags):
        self.flags = flags

    def __enter__(self):
        self._saved = {k: getattr(self._HOMES[k], k) for k in self.flags}
        for k, v in self.flags.items():
            setattr(self._HOMES[k], k, v)
        return self

    def __exit__(self, *exc) -> bool:
        for k, v in self._saved.items():
            setattr(self._HOMES[k], k, v)
        return False


def register_report() -> Dict[str, object]:
    """Mark C1: the register, its offset row against ITS-90's kelvin column,
    above absolute zero and strictly increasing."""
    from ..evaluation import celsius_register_cases as C
    rows = fp.load_fixed_point_register()
    row = sc.declared("fixed_point:temperature_C")
    declared = dict((k, Fraction(v)) for k, v in C.ITS90_CELSIUS)
    kelvin = dict((k, Fraction(v)) for k, v in C.ITS90_KELVIN)
    held = {r.key: r.temperature_C for r in rows}
    carried = {k: sc.apply(row, v) for k, v in held.items()} if row else {}
    exact = all(isinstance(r.temperature_C, Fraction) for r in rows)
    match = [k for k in held if carried.get(k) == kelvin.get(k)]
    values = [r.temperature_C for r in rows]
    increasing = all(a < b for a, b in zip(values, values[1:]))
    positive = all(v > 0 for v in carried.values())
    as_declared = held == declared
    return {"rows": len(rows), "exact": exact, "as_declared": as_declared,
            "offset_row": None if row is None else {
                "factor": str(row.factor), "offset": str(row.offset),
                "unit": row.unit, "quantity": row.quantity},
            "carried_match": len(match), "increasing": increasing,
            "above_absolute_zero": positive,
            "met": (len(rows) == 14 and exact and as_declared
                    and len(match) == 14 and increasing and positive)}


def _order(surface, ops) -> Tuple[str, str]:
    from ..reasoning import coordinate_order as co
    field, left, other, right = ops
    try:
        got = co.order(surface, field, left, right, other_field=other)
    except co.OrderingError as error:
        return error.reason, str(error)
    return got.verdict, got.sentence


def order_report(session) -> Dict[str, object]:
    """Mark C2: the ordering cases, and the offset-dropped verdicts."""
    from ..evaluation.celsius_register_cases import ORDER_CASES
    surface = session.field_surface
    rows = []
    for cid, ops, want in ORDER_CASES:
        got, sentence = _order(surface, ops)
        with switched(OFFSETS=False):
            naive, _s = _order(surface, ops)
        rows.append({"id": cid, "operands": ops, "want": want, "got": got,
                     "ok": got == want, "naive": naive, "sentence": sentence})
    verdicts = ("lt", "gt", "eq")
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows
                         if r["got"] in verdicts and not r["ok"]),
            "rows": rows}


def column_report(session) -> Dict[str, object]:
    """Mark C3: the column cases."""
    from ..evaluation.celsius_register_cases import COLUMN_CASES
    from ..reasoning import column_extremum as cx
    surface = session.field_surface
    rows = []
    for cid, (field, end, table), want in COLUMN_CASES:
        try:
            got = cx.extremum(surface, field, end, table or None)
        except cx.ExtremumError as error:
            outcome: Tuple[str, ...] = (error.reason,)
            read = 0
        else:
            outcome = ("answer",) + tuple(w.row for w in got.winners)
            read = got.rows
        rows.append({"id": cid, "want": list(want), "got": list(outcome),
                     "rows_read": read, "ok": tuple(outcome) == tuple(want)})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "rows": rows}


def _verdict(a) -> Tuple[str, ...]:
    return sw._verdict_of(a)


def _ok(got, want) -> bool:
    return tuple(got[:len(want)]) == tuple(want)


def planner_report(session, before_session=None) -> Dict[str, object]:
    """Mark C4: the planner cases; with the offset-dropped verdicts and, on
    a session built with the register absent, the machine before."""
    from ..evaluation.celsius_register_cases import PLANNER_CASES
    rows = []
    for cid, q, want in PLANNER_CASES:
        got = _verdict(sw.answer(session, q))
        with switched(OFFSETS=False):
            naive = _verdict(sw.answer(session, q))
        routed = router.route(session, q)
        entry = {"id": cid, "want": list(want), "got": list(got),
                 "ok": _ok(got, want), "naive": list(naive),
                 "machine_now": routed.text if routed.answered else None}
        if before_session is not None:
            with switched(ACTIVE=False):
                before = _verdict(sw.answer(before_session, q))
                routed_before = router.route(before_session, q)
            entry["register_absent"] = list(before)
            entry["machine_before"] = (routed_before.text
                                       if routed_before.answered else None)
        rows.append(entry)
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows
                         if r["got"][0] == "ANSWER" and not r["ok"]),
            "answered": sum(1 for r in rows if r["got"][0] == "ANSWER"),
            "machine_answers_now": sum(1 for r in rows
                                       if r["machine_now"] is not None),
            "machine_answered_before": sum(
                1 for r in rows if r.get("machine_before") is not None),
            "register_absent_answers": sum(
                1 for r in rows
                if r.get("register_absent", ["-"])[0] == "ANSWER"),
            "rows": rows}


def control_report(order, planner) -> Dict[str, object]:
    """Mark C5: the offset-dropped control flips the declared verdicts and
    answers every answered planner case wrongly; the register absent
    answers none of the planner questions."""
    from ..evaluation import celsius_register_cases as C
    by_id = {r["id"]: r for r in order["rows"]}
    flips = [cid for cid, r in by_id.items()
             if r["got"] in ("lt", "gt") and r["naive"] in ("lt", "gt")
             and r["naive"] != r["got"]]
    declared_flips = all(cid in flips for cid in C.NAIVE_FLIPS)
    prow = {r["id"]: r for r in planner["rows"]}
    naive_wrong = [(cid, prow[cid]["naive"]) for cid in C.NAIVE_PLANNER_WRONG
                   if prow[cid]["naive"][0] == "ANSWER"
                   and not _ok(prow[cid]["naive"], prow[cid]["want"])]
    absent_answered = planner["register_absent_answers"]
    return {"flips": flips, "declared_flips": list(C.NAIVE_FLIPS),
            "naive_planner_wrong": naive_wrong,
            "naive_planner_declared": len(C.NAIVE_PLANNER_WRONG),
            "register_absent_answers": absent_answered,
            "met": (declared_flips
                    and len(naive_wrong) == len(C.NAIVE_PLANNER_WRONG)
                    and absent_answered == 0)}


def earlier_report(session) -> Dict[str, object]:
    """Mark C6: the scale table's declared questions, the ordering and
    extremum operations' declared sets, the measurand register's corpus and
    Phase 86's corpus, as they were."""
    from . import measurand_register_report as rr
    from . import measurand_report as mr
    table = sc.conversion_report(session)
    reg = rr.register_report(session)
    conv = rr.conversions_report(session)
    charge = rr.charges_report(session)
    p86 = {"kinds": mr.kinds_report(session),
           "temperatures": mr.temperatures_report(session),
           "constants": mr.constants_report(session),
           "amendments": mr.amendments_report(session)}
    held86 = all(v["met"] == v["cases"] for v in p86.values())
    held87 = all(r["met"] == r["cases"] for r in (reg, conv, charge))
    return {"scale_table": {"as_declared": table["as_declared"],
                            "declared": table["declared"]},
            "ordering": {"as_declared": table["ordering_as_declared"],
                         "declared": table["ordering_declared"]},
            "extremum": {"as_declared": table["extremum_as_declared"],
                         "declared": table["extremum_declared"]},
            "measurand_register": {"met": sum(r["met"] for r in
                                              (reg, conv, charge)),
                                   "cases": sum(r["cases"] for r in
                                                (reg, conv, charge))},
            "phase86": {k: {"cases": v["cases"], "met": v["met"]}
                        for k, v in p86.items()},
            "census": rr.census_report(),
            "met": (table["as_declared"] == table["declared"]
                    and table["ordering_as_declared"]
                    == table["ordering_declared"]
                    and table["extremum_as_declared"]
                    == table["extremum_declared"]
                    and held86 and held87)}


def _offset_lie(chain):
    """The chain with its offset conversion's offset dropped, value and both
    columns re-rendered to agree -- a lie the round's own mutation."""
    from dataclasses import replace
    steps = list(chain.steps)
    conv = next((s for s in steps if s.op == "si" and "offset" in s.detail
                 and s.detail.get("kind") == "scale"), None)
    if conv is None:
        return None
    base = steps[conv.inputs[0] - 1].value
    lied = replace(conv, value=base * Fraction(conv.detail["factor"]),
                   detail=dict(conv.detail, offset="0"))
    new = [lied if x is conv else x for x in steps]
    data = ss.chain_data(chain)
    data["steps"][conv.index - 1] = dict(
        lied.as_dict(), column1=ss.sentence(lied),
        column2=ss.equation(lied, new))
    return data


def scripts_report(session, limit: Optional[int] = None) -> Dict[str, object]:
    """Mark C7: every answered planner chain's column-3 script in a fresh
    ``python3 -I``, every mutation of each, and the offset lie."""
    from ..evaluation.celsius_register_cases import PLANNER_CASES
    from .python_tct import run_column3
    from .tct_engine import package_root
    root = str(package_root())
    chains = []
    for cid, q, _want in PLANNER_CASES:
        a = sw.answer(session, q)
        if a.answered:
            chains.append((cid, a.chain))
    if limit is not None:
        chains = chains[:limit]
    verified, failed, aligned, steps = 0, [], 0, 0
    caught = {k: 0 for k in ss.MUTATION_KINDS}
    built = {k: 0 for k in ss.MUTATION_KINDS}
    escaped: List[str] = []
    lies, lies_caught = 0, 0
    for cid, chain in chains:
        got = run_column3(ss.render_script(chain, root))
        steps += len(chain.steps)
        m = re.search(r"ALIGNED (\d+) of (\d+)", got["stdout"])
        aligned += int(m.group(1)) if m else 0
        if got["verified"]:
            verified += 1
        else:
            failed.append(cid)
        for kind, data in ss.mutants(chain).items():
            built[kind] += 1
            bad = run_column3(ss.render_script(chain, root, data))
            if bad["verified"]:
                escaped.append(f"{cid}:{kind}")
            else:
                caught[kind] += 1
        lie = _offset_lie(chain)
        if lie is not None:
            lies += 1
            bad = run_column3(ss.render_script(chain, root, lie))
            if bad["verified"]:
                escaped.append(f"{cid}:offset-lie")
            else:
                lies_caught += 1
    return {"chains": len(chains), "verified": verified, "failed": failed,
            "steps": steps, "aligned": aligned, "mutants": built,
            "caught": caught, "offset_lies": lies,
            "offset_lies_caught": lies_caught, "escaped": escaped,
            "met": (verified == len(chains) and not escaped
                    and lies == len(chains) and lies_caught == lies)}


def agreement_report(session) -> Dict[str, object]:
    """Reported, not scored: each fixed point carried into kelvins against
    the element register's melting point of the same element."""
    surface = session.field_surface
    row = sc.declared("fixed_point:temperature_C")
    out = []
    for point in fp.load_fixed_point_register():
        sym = point.substance.replace("e-H2", "H").rstrip("2")
        if sym == "H2O" or point.substance == "H2O":
            continue
        try:
            held = surface.field("melting_point_K", sym)
        except Exception:                           # pragma: no cover
            continue
        kelvin = sc.apply(row, point.temperature_C)
        gap = Fraction(held.value) - kelvin
        out.append({"point": point.key, "element": held.row,
                    "its90_K": str(kelvin), "element_K": str(held.value),
                    "gap_K": str(gap),
                    "within_hundredth": abs(gap) <= Fraction(1, 200)})
    within = [r for r in out if r["within_hundredth"]]
    return {"compared": len(out), "within_rounding": len(within),
            "outside": [(r["point"], r["gap_K"]) for r in out
                        if not r["within_hundredth"]],
            "rows": out}


def celsius_register_report(scripts: bool = True) -> Dict[str, object]:
    """The whole measurement of ``studies/CELSIUS_REGISTER_STUDY.md``."""
    from .session import GeometricSession
    session = GeometricSession()
    with switched(ACTIVE=False):
        before = GeometricSession()
        before.field_surface.tables()
    order = order_report(session)
    planner = planner_report(session, before)
    report: Dict[str, object] = {
        "register": register_report(),
        "order": order,
        "column": column_report(session),
        "planner": planner,
        "control": control_report(order, planner),
        "earlier": earlier_report(session),
        "agreement": agreement_report(session),
        "study": "studies/CELSIUS_REGISTER_STUDY.md",
        "lean_file": "RequestProject/GLM/CelsiusRegister.lean",
    }
    if scripts:
        report["scripts"] = scripts_report(session)
    return report
