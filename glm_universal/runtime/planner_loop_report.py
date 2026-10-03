"""``glm_universal.runtime.planner_loop_report`` -- the measurement of the
loop-through-the-planner round.

``studies/PLANNER_LOOP_STUDY.md`` (Phase 88) declares eight marks over the
corpus of :mod:`glm_universal.evaluation.planner_loop_cases`; this module
takes the seven that are measured (the eighth is the Lean file,
``RequestProject/GLM/PlannerLoop.lean``).  The bridge itself is
:mod:`glm_universal.runtime.planner_bridge`; the dialect's three builtins are
``b_derive``, ``b_ask`` and ``b_solve`` of
:mod:`glm_universal.reasoning.python_speech`.

Two controls: **bridge off** (the dialect alone, as the reasoning layer runs
it: every call refuses ``BRIDGE_UNAVAILABLE``) and **before** (the router
with the bridge and the frames switched off -- ``router.BRIDGE`` and
``router.FRAMES`` -- which is the machine as the round found it for every
case of the corpus).  A third reading, not a mark, asks the router the
English questions the loop programs answer (item 9, the utility gate).
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from . import router
from .planner_bridge import PlannerBridge, mutated_records

__all__ = ["switched", "program_rows", "frames_report", "census_report",
           "scripts_report", "earlier_report", "paraphrase_report",
           "planner_loop_report"]


class switched:
    """The router's switches set for a control, and restored after."""

    def __init__(self, **flags):
        self.flags = flags

    def __enter__(self):
        self._saved = {k: getattr(router, k) for k in self.flags}
        for k, v in self.flags.items():
            setattr(router, k, v)
        return self

    def __exit__(self, *exc) -> bool:
        for k, v in self._saved.items():
            setattr(router, k, v)
        return False


def _verdict(p) -> Tuple[str, ...]:
    return ("ANSWER", p.value_literal) if p.answered else ("REFUSED",
                                                          p.refusal)


def program_rows(session, cases, bridge: PlannerBridge) -> Dict[str, object]:
    """Marks W1-W3 and the program half of W6 over one group of cases."""
    from ..reasoning import python_speech as sp
    rows = []
    for cid, src, want in cases:
        got = _verdict(sp.speak(src, bridge=bridge))
        alone = _verdict(sp.speak(src))
        routed = router.route(session, src)
        with switched(BRIDGE=False, FRAMES=False):
            before = router.route(session, src)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": tuple(got) == tuple(want),
                     "bridge_off": list(alone),
                     "machine_now": routed.text if routed.answered else None,
                     "machine_before": before.text if before.answered
                     else None})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows if r["got"][0] == "ANSWER"
                         and not r["ok"]),
            "answered": sum(1 for r in rows if r["got"][0] == "ANSWER"),
            "bridge_off_answers": sum(1 for r in rows
                                      if r["bridge_off"][0] == "ANSWER"),
            "machine_answered_before": sum(1 for r in rows
                                           if r["machine_before"]),
            "machine_answers_now": sum(1 for r in rows if r["machine_now"]),
            "rows": rows}


def frames_report(session) -> Dict[str, object]:
    """Mark W4, first half: every frame case through the router."""
    from ..evaluation.planner_loop_cases import FRAME_CASES
    rows = []
    for cid, q, want in FRAME_CASES:
        r = router.route(session, q)
        surface = router.reader_of(q)
        if want[0] == "SURFACE":
            ok = surface == want[1]
            got = ["SURFACE", surface]
        else:
            got = (["ANSWER", r.text] if r.answered else
                   ["REFUSED", r.text.split(":")[1].strip()
                    if r.text.startswith("refused:") else r.text])
            ok = surface == "python" and tuple(got) == tuple(want)
        with switched(BRIDGE=False, FRAMES=False):
            before = router.route(session, q)
        rows.append({"id": cid, "want": list(want), "got": got, "ok": ok,
                     "machine_before": before.text if before.answered
                     else None,
                     "machine_now": r.text if r.answered else None})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows if r["got"][0] == "ANSWER"
                         and not r["ok"]),
            "machine_answered_before": sum(1 for r in rows
                                           if r["machine_before"]),
            "machine_answers_now": sum(1 for r in rows if r["machine_now"]),
            "rows": rows}


def _earlier_texts() -> Dict[str, List[str]]:
    from ..evaluation import stepwise_cases as s1
    from ..evaluation import stepwise_two_cases as s2
    out = dict(router._declared_sets())
    out["stepwise"] = [c[1] for c in (s1.COMPOSITION_CASES + s1.GOAL_CASES
                                      + s1.NARRATIVE_CASES)]
    texts = []
    for name in dir(s2):
        if name.endswith("_CASES"):
            for c in getattr(s2, name):
                if isinstance(c, tuple) and len(c) > 1 and isinstance(
                        c[1], str):
                    texts.append(c[1])
    out["stepwise_two"] = texts
    return out


def census_report() -> Dict[str, object]:
    """Mark W4, second half: on the earlier declared question sets, the
    frames change the reading surface of no question."""
    moved: List[Tuple[str, str, str, str]] = []
    counted = 0
    for name, texts in _earlier_texts().items():
        for t in texts:
            counted += 1
            now = router.reader_of(t)
            with switched(FRAMES=False):
                was = router.reader_of(t)
            if now != was:
                moved.append((name, t, was, now))
    return {"questions": counted, "moved": moved, "met": not moved}


def _failed_check(stdout: str) -> int:
    m = re.search(r"FAILED check (\d+)", stdout)
    return int(m.group(1)) if m else 0


def scripts_report(session, bridge: PlannerBridge,
                   limit: Optional[int] = None) -> Dict[str, object]:
    """Mark W5: every answered bridge program's column 3 in a fresh
    ``python3 -I`` (re-running each sub-answer's own script), and every
    declared mutation of each."""
    from ..evaluation import planner_loop_cases as C
    from ..reasoning import python_speech as sp
    from .python_tct import run_column3
    programs, verified, failed, subs = 0, 0, [], 0
    caught = {k: 0 for k in C.MUTATION_KINDS}
    built = {k: 0 for k in C.MUTATION_KINDS}
    where: Dict[str, List[int]] = {k: [] for k in C.MUTATION_KINDS}
    escaped: List[str] = []
    for cid, src, _want in (C.DERIVE_CASES + C.ASK_CASES + C.SOLVE_CASES
                            + C.LOOP_CASES):
        if cid not in C.BRIDGE_CASES:
            continue
        if limit is not None and programs >= limit:
            break
        p = sp.speak(src, bridge=bridge)
        if not p.answered:
            continue
        programs += 1
        subs += len(p.bridge)
        got = run_column3(p.column3)
        if got["verified"]:
            verified += 1
        else:
            failed.append(cid)
        for kind in C.MUTATION_KINDS:
            if kind == "answer":
                script = sp.mutated_script(p)
            else:
                recs = mutated_records(p.bridge, kind, bridge.root)
                script = sp.render_script(p, bridge=recs)
            built[kind] += 1
            bad = run_column3(script)
            if bad["verified"]:
                escaped.append(f"{cid}:{kind}")
            else:
                caught[kind] += 1
                where[kind].append(_failed_check(bad["stdout"]))
    return {"programs": programs, "verified": verified, "failed": failed,
            "sub_scripts": subs, "mutants": built, "caught": caught,
            "caught_at_check": {k: sorted(set(v)) for k, v in where.items()},
            "escaped": escaped,
            "met": (verified == programs and not escaped
                    and all(caught[k] == built[k] for k in built))}


def earlier_report(session) -> Dict[str, object]:
    """Mark W7: the dialect's declared cases and battery, and the stepwise
    planner's earlier rounds, as they were."""
    from ..evaluation import python_speech_cases as P
    from ..reasoning import python_speech as sp
    ns: Dict[str, object] = {}
    exec(sp.ps.PRELUDE, ns)
    value_wrong = []
    for cid, src in P.VALUE_CASES:
        p = sp.speak(src)
        try:
            ref = ns["run_source"](src)
            ok = p.answered and ns["same"](eval(p.value_literal, ns), ref)
        except Exception:                                   # noqa: BLE001
            ok = False
        if not ok:
            value_wrong.append(cid)
    refusal_moved = [cid for cid, src, name in P.REFUSAL_CASES
                     if sp.speak(src).refusal != name]
    battery = sp.differential_battery()
    from . import measurand_register_report as mrr
    below = mrr.earlier_report(session)
    return {"python_values": len(P.VALUE_CASES),
            "python_values_moved": value_wrong,
            "python_refusals": len(P.REFUSAL_CASES),
            "python_refusals_moved": refusal_moved,
            "battery_total": battery["total"],
            "battery_wrong": battery["wrong"],
            "stepwise_earlier_held": below["met"],
            "met": (not value_wrong and not refusal_moved
                    and battery["wrong"] == 0 and below["met"])}


def paraphrase_report(session) -> Dict[str, object]:
    """The reading of item 9 (the utility gate): the English questions the
    loop programs answer, asked of the router directly."""
    from ..evaluation.planner_loop_cases import ENGLISH_PARAPHRASES
    rows = []
    for cid, q in ENGLISH_PARAPHRASES:
        r = router.route(session, q)
        rows.append({"id": cid, "question": q, "surface": r.surface,
                     "answered": r.answered, "text": r.text[:160]})
    return {"questions": len(rows),
            "answered": sum(r["answered"] for r in rows), "rows": rows}


def planner_loop_report(scripts: bool = True) -> Dict[str, object]:
    """The whole measurement of ``studies/PLANNER_LOOP_STUDY.md``."""
    from ..evaluation import planner_loop_cases as C
    from .session import GeometricSession
    session = GeometricSession()
    bridge = PlannerBridge(session)
    groups = {"derive": C.DERIVE_CASES, "ask": C.ASK_CASES,
              "solve": C.SOLVE_CASES, "loop": C.LOOP_CASES}
    report: Dict[str, object] = {k: program_rows(session, v, bridge)
                                 for k, v in groups.items()}
    report["frames"] = frames_report(session)
    report["census"] = census_report()
    report["earlier"] = earlier_report(session)
    report["paraphrases"] = paraphrase_report(session)
    bridged = [r for k in groups for r in report[k]["rows"]
               if r["id"] in C.BRIDGE_CASES]
    report["bridge_off"] = {
        "bridge_cases": len(bridged),
        "answered": sum(1 for r in bridged if r["bridge_off"][0] == "ANSWER"),
        "refused_by_name": sum(1 for r in bridged
                               if r["bridge_off"][0] == "REFUSED"),
        "unavailable": sum(1 for r in bridged
                           if r["bridge_off"][1] == "BRIDGE_UNAVAILABLE")}
    answer_rows = [r for k in groups for r in report[k]["rows"]
                   if r["want"][0] == "ANSWER"] + [
        r for r in report["frames"]["rows"] if r["want"][0] == "ANSWER"]
    report["machine"] = {
        "answer_cases": len(answer_rows),
        "answered_now": sum(1 for r in answer_rows if r["machine_now"]),
        "answered_before": sum(1 for r in answer_rows
                               if r["machine_before"]),
        "bridge_cases_answered_before": sum(1 for r in bridged
                                            if r["machine_before"])}
    report["bridge_calls"] = bridge.calls
    report["study"] = "studies/PLANNER_LOOP_STUDY.md"
    report["lean_file"] = "RequestProject/GLM/PlannerLoop.lean"
    if scripts:
        report["scripts"] = scripts_report(session, bridge)
    return report
