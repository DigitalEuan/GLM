"""``glm_universal.runtime.measurand_report`` -- the measurement of the
measurands round.

``studies/MEASURANDS_STUDY.md`` (Phase 86) declares seven marks over the
corpus of :mod:`glm_universal.evaluation.measurand_cases`; this module takes
the six that are measured (the seventh is the Lean file,
``RequestProject/GLM/MeasurandKinds.lean``).  The kinds themselves live in
:mod:`glm_universal.runtime.measurands`, and the planner reads them in
:mod:`glm_universal.runtime.stepwise` (``_kind_check``, ``_kind_failure``,
the offset reading in ``goal_two`` and the constants in ``_goal_core``).

One control: **kinds off** -- the same modules with
:data:`glm_universal.runtime.measurands.ACTIVE` switched off, which is the
dimension check alone, as rounds two to four had it (marks M1-M4).
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from . import measurands as ms
from . import router
from . import stepwise as sw
from ..reasoning import stepwise_script as ss

__all__ = ["kinds_off", "kinds_report", "temperatures_report",
           "constants_report", "control_report", "amendments_report",
           "answered_chains", "scripts_report", "interference_report",
           "measurand_report"]


class kinds_off:
    """The planner with the kinds of quantity switched off.

    Used as ``with kinds_off(): ...``; the flag is restored."""

    def __enter__(self):
        self._saved = ms.ACTIVE
        ms.ACTIVE = False
        return self

    def __exit__(self, *exc) -> bool:
        ms.ACTIVE = self._saved
        return False


def _verdict(a) -> Tuple[str, ...]:
    return sw._verdict_of(a)


def _ok(got, want) -> bool:
    return tuple(got[:len(want)]) == tuple(want)


def _rows(session, cases) -> Dict[str, object]:
    rows = []
    for cid, q, want in cases:
        a = sw.answer(session, q)
        with kinds_off():
            before = sw.answer(session, q)
            routed_before = router.route(session, q)
        routed = router.route(session, q)
        got = _verdict(a)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _ok(got, want),
                     "kinds_off": list(_verdict(before)),
                     "machine_before": routed_before.text if
                     routed_before.answered else None,
                     "machine_now": routed.text if routed.answered else None})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows
                         if r["got"][0] == "ANSWER" and not r["ok"]),
            "answered": sum(1 for r in rows if r["got"][0] == "ANSWER"),
            "kinds_off_answers": sum(1 for r in rows
                                     if r["kinds_off"][0] == "ANSWER"),
            "machine_answered_before": sum(1 for r in rows
                                           if r["machine_before"] is not None),
            "machine_answers_now": sum(1 for r in rows
                                       if r["machine_now"] is not None),
            "rows": rows}


def kinds_report(session) -> Dict[str, object]:
    """Mark M1: kinds of quantity on units."""
    from ..evaluation.measurand_cases import KIND_CASES
    return _rows(session, KIND_CASES)


def temperatures_report(session) -> Dict[str, object]:
    """Mark M2: temperature levels and differences."""
    from ..evaluation.measurand_cases import TEMPERATURE_CASES
    return _rows(session, TEMPERATURE_CASES)


def constants_report(session) -> Dict[str, object]:
    """Mark M3: the SI's defining constants supplied."""
    from ..evaluation.measurand_cases import CONSTANT_CASES
    return _rows(session, CONSTANT_CASES)


def control_report(session, kinds=None, temps=None,
                   consts=None) -> Dict[str, object]:
    """Mark M4: what the kinds-off control does with the corpus: the
    ``KIND_MISMATCH`` refusals it answers (and with what), the kind and
    temperature refusals it answers, and the new answers it gives."""
    from ..evaluation.measurand_cases import CONTROL_KIND_ANSWERS_AT_LEAST
    kinds = kinds or kinds_report(session)
    temps = temps or temperatures_report(session)
    consts = consts or constants_report(session)
    rows = kinds["rows"] + temps["rows"] + consts["rows"]
    kind_answered = [(r["id"], r["kinds_off"][1]) for r in kinds["rows"]
                     if r["want"] == ["REFUSED", "KIND_MISMATCH"]
                     and r["kinds_off"][0] == "ANSWER"]
    refusals_answered = [r["id"] for r in rows if r["want"][0] == "REFUSED"
                         and r["want"][1] in (
                             "KIND_MISMATCH", "LEVEL_AS_DIFFERENCE",
                             "DIFFERENCE_AS_LEVEL", "KIND_CONFLATION",
                             "BELOW_ABSOLUTE_ZERO")
                         and r["kinds_off"][0] == "ANSWER"]
    new_answers = [r["id"] for r in rows if r["want"][0] == "ANSWER"
                   and r["kinds_off"][0] != "ANSWER"]
    same = [r["id"] for r in rows if r["want"][0] == "ANSWER"
            and r["kinds_off"] == r["want"]]
    return {"kind_refusals_answered": kind_answered,
            "kind_refusals_answered_at_least": CONTROL_KIND_ANSWERS_AT_LEAST,
            "refusals_answered": refusals_answered,
            "new_answers": new_answers, "unchanged_answers": same,
            "met": len(kind_answered) >= CONTROL_KIND_ANSWERS_AT_LEAST}


def amendments_report(session) -> Dict[str, object]:
    """The earlier declared cases this round amends: each gets its amended
    verdict with the kinds on and its original verdict with them off."""
    from ..evaluation import stepwise_two_cases as C2
    from ..evaluation.measurand_cases import AMENDED
    originals = {c[0]: c for c in (C2.ORIGINAL_UNIT_CASES
                                   + C2.ORIGINAL_REGISTER_CASES
                                   + C2.ORIGINAL_NARRATIVE_CASES)}
    rows = []
    for (module, cid), (want, _why) in AMENDED.items():
        q, old = originals[cid][1], originals[cid][2]
        now = _verdict(sw.answer(session, q))
        with kinds_off():
            before = _verdict(sw.answer(session, q))
        rows.append({"id": cid, "module": module, "original": list(old),
                     "amended": list(want), "now": list(now),
                     "kinds_off": list(before),
                     "ok": _ok(now, want) and _ok(before, old)})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "rows": rows}


# ---------------------------------------------------------------------------
# the scripts (mark M5)
# ---------------------------------------------------------------------------

def answered_chains(session) -> List[Tuple[str, object]]:
    """Every answered chain of the corpus, with its case id."""
    from ..evaluation import measurand_cases as C
    out = []
    for cid, q, _want in (C.KIND_CASES + C.TEMPERATURE_CASES
                          + C.CONSTANT_CASES):
        a = sw.answer(session, q)
        if a.answered:
            out.append((cid, a.chain))
    return out


def scripts_report(session, limit: Optional[int] = None) -> Dict[str, object]:
    """Every answered chain's column-3 script in a fresh ``python3 -I``, and
    every mutation of each."""
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


# ---------------------------------------------------------------------------
# non-interference (mark M6)
# ---------------------------------------------------------------------------

def interference_report(session) -> Dict[str, object]:
    """Round four's measurement, and through it rounds one to three and the
    router's declared sets, re-taken with the kinds on (scripts off)."""
    from . import stepwise_four as sw4
    from . import stepwise_two as sw2
    four = {
        "orders": sw4.orders_report(session),
        "bounded": sw4.bounded_report(session),
        "ranks": sw4.ranks_report(session),
        "present": sw4.present_report(session),
        "follow_ups": sw4.follow_ups_report(session),
    }
    below = sw4.interference_report(session)
    two = {"units": sw2.units_report(session),
           "register": sw2.register_report(session),
           "narratives": sw2.narratives_report(session)}
    held_four = all(v["met"] == v["cases"] for v in four.values())
    return {"round_four": {k: {"cases": v["cases"], "met": v["met"]}
                           for k, v in four.items()},
            "round_four_held": held_four,
            "round_three_held": below["round_three_held"],
            "round_two_goals": {k: {"cases": v["cases"], "met": v["met"]}
                                for k, v in two.items()},
            "round_two_held": below["round_two_held"],
            "round_one_held": below["round_one_held"],
            "router_read": below["router_read"],
            "router_questions": below["router_questions"],
            "turned_into_answers": below["turned_into_answers"],
            "declared_refusals_answered": below["declared_refusals_answered"]}


def measurand_report(scripts: bool = True) -> Dict[str, object]:
    """The whole measurement of ``studies/MEASURANDS_STUDY.md``."""
    from .session import GeometricSession
    session = GeometricSession()
    kinds = kinds_report(session)
    temps = temperatures_report(session)
    consts = constants_report(session)
    report: Dict[str, object] = {
        "kinds": kinds, "temperatures": temps, "constants": consts,
        "control": control_report(session, kinds, temps, consts),
        "amendments": amendments_report(session),
        "interference": interference_report(session),
        "study": "studies/MEASURANDS_STUDY.md",
        "lean_file": "RequestProject/GLM/MeasurandKinds.lean",
    }
    if scripts:
        report["scripts"] = scripts_report(session)
    return report
