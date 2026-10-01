"""``glm_universal.runtime.measurand_register_report`` -- the measurement of
the measurand-register round.

``studies/MEASURAND_REGISTER_STUDY.md`` (Phase 87) declares eight marks over
the corpus of :mod:`glm_universal.evaluation.measurand_register_cases`; this
module takes the seven that are measured (the eighth is the Lean file,
``RequestProject/GLM/MeasurandRegister.lean``).  The register itself lives in
:mod:`glm_universal.runtime.measurand_register`, and the planner reads it in
:mod:`glm_universal.runtime.stepwise` (``goal_two``, ``_register_reading``,
the conversion laws in ``_LAWS_IN_SCOPE`` and the wheel restriction in
``_goal_core``).

Three controls: **register off** (Phase 86's planner, for the machine
before the round), **naive** (each conversion read as an identity with the
efficiency dropped) and **unrestricted** (a register measurand read by name
feeds every wheel's copy of its quantity).
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from . import measurand_register as mreg
from . import router
from . import stepwise as sw
from ..reasoning import stepwise_script as ss

__all__ = ["switched", "register_report", "conversions_report",
           "charges_report", "control_report", "earlier_report",
           "answered_chains", "scripts_report", "census_report",
           "measurand_register_report"]


class switched:
    """The register's switches set for a control, and restored after:
    ``with switched(ACTIVE=False): ...``."""

    def __init__(self, **flags):
        self.flags = flags

    def __enter__(self):
        self._saved = {k: getattr(mreg, k) for k in self.flags}
        for k, v in self.flags.items():
            setattr(mreg, k, v)
        return self

    def __exit__(self, *exc) -> bool:
        for k, v in self._saved.items():
            setattr(mreg, k, v)
        return False


def _verdict(a) -> Tuple[str, ...]:
    return sw._verdict_of(a)


def _ok(got, want) -> bool:
    return tuple(got[:len(want)]) == tuple(want)


def _rows(session, cases) -> Dict[str, object]:
    rows = []
    for cid, q, want in cases:
        got = _verdict(sw.answer(session, q))
        with switched(ACTIVE=False):
            before = _verdict(sw.answer(session, q))
            routed_before = router.route(session, q)
        with switched(NAIVE=True):
            naive = _verdict(sw.answer(session, q))
        with switched(RESTRICT=False):
            free = _verdict(sw.answer(session, q))
        routed = router.route(session, q)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _ok(got, want),
                     "register_off": list(before), "naive": list(naive),
                     "unrestricted": list(free),
                     "machine_before": routed_before.text if
                     routed_before.answered else None,
                     "machine_now": routed.text if routed.answered else None})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows
                         if r["got"][0] == "ANSWER" and not r["ok"]),
            "answered": sum(1 for r in rows if r["got"][0] == "ANSWER"),
            "register_off_answers": sum(1 for r in rows
                                        if r["register_off"][0] == "ANSWER"),
            "machine_answered_before": sum(1 for r in rows
                                           if r["machine_before"] is not None),
            "machine_answers_now": sum(1 for r in rows
                                       if r["machine_now"] is not None),
            "rows": rows}


def register_report(session) -> Dict[str, object]:
    """Mark R1: register values read through their measurand."""
    from ..evaluation.measurand_register_cases import REGISTER_CASES
    return _rows(session, REGISTER_CASES)


def conversions_report(session) -> Dict[str, object]:
    """Mark R2: conversions through a stated efficiency."""
    from ..evaluation.measurand_register_cases import CONVERSION_CASES
    return _rows(session, CONVERSION_CASES)


def charges_report(session) -> Dict[str, object]:
    """Mark R3: the elementary charge as a unit."""
    from ..evaluation.measurand_register_cases import CHARGE_CASES
    return _rows(session, CHARGE_CASES)


def control_report(session, reg=None, conv=None) -> Dict[str, object]:
    """Mark R4: the naive control answers the conversion cases wrongly, and
    the unrestricted control answers the declared restriction case."""
    from ..evaluation import measurand_register_cases as C
    reg = reg or register_report(session)
    conv = conv or conversions_report(session)
    naive_wrong = [(r["id"], r["naive"][1]) for r in conv["rows"]
                   if r["want"][0] == "ANSWER" and r["naive"][0] == "ANSWER"
                   and not _ok(r["naive"], r["want"])]
    naive_right = [r["id"] for r in conv["rows"]
                   if r["want"][0] == "ANSWER" and _ok(r["naive"], r["want"])]
    free = {r["id"]: r for r in reg["rows"]}
    unrestricted = [(cid, free[cid]["unrestricted"])
                    for cid in C.UNRESTRICTED_WRONG]
    free_met = all(v[0] == "ANSWER" for _cid, v in unrestricted)
    return {"naive_wrong": naive_wrong, "naive_right": naive_right,
            "naive_wrong_at_least": C.NAIVE_WRONG_AT_LEAST,
            "unrestricted": unrestricted,
            "met": (len(naive_wrong) >= C.NAIVE_WRONG_AT_LEAST
                    and not naive_right and free_met)}


def earlier_report(session) -> Dict[str, object]:
    """Mark R5: Phase 86's corpus and rounds one to four, unchanged."""
    from . import measurand_report as mr
    p86 = {"kinds": mr.kinds_report(session),
           "temperatures": mr.temperatures_report(session),
           "constants": mr.constants_report(session),
           "amendments": mr.amendments_report(session)}
    below = mr.interference_report(session)
    held86 = all(v["met"] == v["cases"] for v in p86.values())
    return {"phase86": {k: {"cases": v["cases"], "met": v["met"]}
                        for k, v in p86.items()},
            "phase86_held": held86,
            "round_four_held": below["round_four_held"],
            "round_three_held": below["round_three_held"],
            "round_two_held": below["round_two_held"],
            "round_one_held": below["round_one_held"],
            "router_read": below["router_read"],
            "router_questions": below["router_questions"],
            "met": (held86 and below["round_four_held"]
                    and below["round_three_held"]
                    and below["round_two_held"]
                    and below["round_one_held"])}


def answered_chains(session) -> List[Tuple[str, object]]:
    """Every answered chain of the corpus, with its case id."""
    from ..evaluation import measurand_register_cases as C
    out = []
    for cid, q, _want in (C.REGISTER_CASES + C.CONVERSION_CASES
                          + C.CHARGE_CASES):
        a = sw.answer(session, q)
        if a.answered:
            out.append((cid, a.chain))
    return out


def scripts_report(session, limit: Optional[int] = None) -> Dict[str, object]:
    """Mark R6: every answered chain's column-3 script in a fresh
    ``python3 -I``, and every mutation of each."""
    from .python_tct import run_column3
    from .tct_engine import package_root
    root = str(package_root())
    chains = answered_chains(session)
    if limit is not None:
        chains = chains[:limit]
    verified, failed, aligned, steps = 0, [], 0, 0
    caught = {k: 0 for k in ss.MUTATION_KINDS}
    built = {k: 0 for k in ss.MUTATION_KINDS}
    escaped: List[str] = []
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
    return {"chains": len(chains), "verified": verified, "failed": failed,
            "steps": steps, "aligned": aligned, "mutants": built,
            "caught": caught, "escaped": escaped}


def census_report() -> Dict[str, object]:
    """Mark R7: the unit table's related pairs, read against the register."""
    got = mreg.comparability_census()
    got["met"] = (not got["withdrawn"] and not got["unregistered"]
                  and got["same_kind"] == got["related_pairs"])
    return got


def measurand_register_report(scripts: bool = True) -> Dict[str, object]:
    """The whole measurement of ``studies/MEASURAND_REGISTER_STUDY.md``."""
    from .session import GeometricSession
    session = GeometricSession()
    reg = register_report(session)
    conv = conversions_report(session)
    charge = charges_report(session)
    report: Dict[str, object] = {
        "register": reg, "conversions": conv, "charges": charge,
        "control": control_report(session, reg, conv),
        "earlier": earlier_report(session),
        "census": census_report(),
        "study": "studies/MEASURAND_REGISTER_STUDY.md",
        "lean_file": "RequestProject/GLM/MeasurandRegister.lean",
    }
    if scripts:
        report["scripts"] = scripts_report(session)
    return report
