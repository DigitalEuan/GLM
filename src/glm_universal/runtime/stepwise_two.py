"""``glm_universal.runtime.stepwise_two`` -- the measurement of round two of
the stepwise planner.

``studies/STEPWISE_TWO_STUDY.md`` (Phase 73) declares eight marks over the
corpus of :mod:`glm_universal.evaluation.stepwise_two_cases`; this module
takes the seven that are measured (the eighth is the Lean file).  The frames,
the unit reading and the register feed themselves live where they run: in
:mod:`glm_universal.runtime.stepwise` (the grammar and the goal mode),
:mod:`glm_universal.runtime.quantity_units` (the declared unit table) and
:mod:`glm_universal.reasoning.stepwise_script` (the three columns of the new
steps).

Two controls:

* **Round one's reader** -- the same module with
  :data:`glm_universal.runtime.stepwise.ROUND_TWO` switched off, which is
  what the corpus met before this round (mark T1's control).
* **Strip the units** -- every amount read as if it were SI, every target
  unit ignored, every register value taken as held, then round one's goal
  mode (mark T4).  It is the reading the unit table exists to prevent.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from . import stepwise as sw
from ..reasoning import stepwise_script as ss

__all__ = ["round_one_reader", "strip_units", "frames_report",
           "units_report", "register_report", "controls_report",
           "narratives_report", "follow_ups_report", "scripts_report",
           "interference_report", "stepwise_two_report", "answered_chains"]


class round_one_reader:
    """The stepwise planner as round one left it: round two switched off.

    Used as ``with round_one_reader(): ...``; the flag is restored on exit.
    """

    def __enter__(self):
        self._saved = sw.ROUND_TWO
        sw.ROUND_TWO = False
        return self

    def __exit__(self, *exc) -> bool:
        sw.ROUND_TWO = self._saved
        return False


def _verdict(a) -> Tuple[str, ...]:
    return sw._verdict_of(a)


def _ok(got, want) -> bool:
    return tuple(got[:len(want)]) == tuple(want)


def frames_report(session) -> Dict[str, object]:
    """Mark T1: the frame cases, and round one's reader on the same."""
    from ..evaluation.stepwise_two_cases import FRAME_CASES
    rows = []
    for cid, q, want in FRAME_CASES:
        a = sw.answer(session, q)
        with round_one_reader():
            before = sw.answer(session, q)
        got = _verdict(a)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _ok(got, want),
                     "round_one": list(_verdict(before))})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows
                         if r["got"][0] == "ANSWER" and not r["ok"]),
            "round_one_answers": sum(1 for r in rows
                                     if r["round_one"][0] == "ANSWER"),
            "rows": rows}


def _goal_rows(session, cases) -> Dict[str, object]:
    rows = []
    for cid, q, want, stitch in cases:
        a = sw.answer(session, q)
        with round_one_reader():
            before = sw.answer(session, q)
        got = _verdict(a)
        ok = _ok(got, want) and (not a.answered
                                 or sw.stitched_of(a) == stitch)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "stitched": list(sw.stitched_of(a)),
                     "want_stitched": list(stitch), "ok": ok,
                     "round_one": list(_verdict(before))})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows
                         if r["got"][0] == "ANSWER" and not r["ok"]),
            "round_one_answers": sum(1 for r in rows
                                     if r["round_one"][0] == "ANSWER"),
            "rows": rows}


def units_report(session) -> Dict[str, object]:
    """Mark T2: givens (and targets) written with units."""
    from ..evaluation.stepwise_two_cases import UNIT_CASES
    return _goal_rows(session, UNIT_CASES)


def register_report(session) -> Dict[str, object]:
    """Mark T3: register values fed to the wheels."""
    from ..evaluation.stepwise_two_cases import REGISTER_CASES
    return _goal_rows(session, REGISTER_CASES)


# ---------------------------------------------------------------------------
# the strip-the-units control (mark T4)
# ---------------------------------------------------------------------------

def strip_units(session, text: str) -> Optional[str]:
    """The question with every unit dropped and every register phrase
    replaced by the number the register holds, as written; None when there
    is nothing to strip to (a bare register phrase names no quantity)."""
    parsed = sw.parse_goal_two(text)
    if parsed is None:
        return None
    givens, targets, verb, _ = parsed
    leaves = sw.Leaves(session)
    parts = []
    for name, spec in givens:
        if name is None:
            return None
        if spec[0] in ("num", "unit"):
            parts.append(f"{name.replace('_', ' ')} = "
                         f"{ss.render_value(spec[1])}")
            continue
        try:
            _op, value, _d = leaves.get(spec[1])
        except sw.Refused:
            return None
        parts.append(f"{name.replace('_', ' ')} = {ss.render_value(value)}")
    asked = ", then the ".join(t.replace("_", " ") for t, _ in targets)
    return f"given {', '.join(parts)}, {verb} the {asked}"


def controls_report(session) -> Dict[str, object]:
    """Mark T4: what the strip-the-units reading answers."""
    from ..evaluation.stepwise_two_cases import (
        NAIVE_REFUSALS_ANSWERED_AT_LEAST, NAIVE_WRONG_AT_LEAST,
        REGISTER_CASES, UNIT_CASES)
    unit_refusals = {"UNKNOWN_UNIT", "UNIT_MISMATCH", "UNIT_INEXACT",
                     "OFFSET_UNIT", "SCALE_UNDECLARED"}
    rows = []
    for cid, q, want, _ in UNIT_CASES + REGISTER_CASES:
        stripped = strip_units(session, q)
        naive = None
        if stripped is not None:
            with round_one_reader():
                got = sw.answer(session, stripped)
            naive = got.value if got.answered else None
        rows.append({"id": cid, "want": list(want), "stripped": stripped,
                     "naive": naive})
    wrong = [r["id"] for r in rows if r["want"][0] == "ANSWER"
             and r["naive"] is not None and r["naive"] != r["want"][1]]
    coincide = [r["id"] for r in rows if r["want"][0] == "ANSWER"
                and r["naive"] == r["want"][1]]
    answered_refusals = [r["id"] for r in rows if r["want"][0] == "REFUSED"
                         and r["want"][1] in unit_refusals
                         and r["naive"] is not None]
    return {"naive_wrong": wrong, "naive_coincides": coincide,
            "naive_answers_unit_refusals": answered_refusals,
            "wrong_at_least": NAIVE_WRONG_AT_LEAST,
            "refusals_at_least": NAIVE_REFUSALS_ANSWERED_AT_LEAST,
            "met": (len(wrong) >= NAIVE_WRONG_AT_LEAST and
                    len(answered_refusals) >=
                    NAIVE_REFUSALS_ANSWERED_AT_LEAST),
            "rows": rows}


# ---------------------------------------------------------------------------
# narratives, follow-ups (mark T7)
# ---------------------------------------------------------------------------

def _stated_values(a) -> Dict[str, str]:
    """Each asked quantity's value as the chain states it: in the unit asked
    for when one was, else in SI."""
    vals: Dict[str, str] = {}
    if not a.chain:
        return vals
    for s in a.chain.steps:
        if s.op == "axiom" and s.origin != "stitched":
            vals.setdefault(s.label, ss.render_value(s.value))
    for s in a.chain.steps:
        if s.op == "unit_out":
            vals[s.label] = ss.render_value(s.value)
    return vals


def narratives_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_two_cases import NARRATIVE_CASES
    rows = []
    for cid, q, want, values, order, stitch in NARRATIVE_CASES:
        a = sw.answer(session, q)
        got = _verdict(a)
        vals = _stated_values(a)
        ok = got[0] == want[0] and vals == values and \
            sw.taken_order(a) == order and sw.stitched_of(a) == stitch
        rows.append({"id": cid, "got": list(got), "values": vals,
                     "order": list(sw.taken_order(a)),
                     "stitched": list(sw.stitched_of(a)), "ok": ok})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "rows": rows}


def follow_ups_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_two_cases import FOLLOW_UP_CASES
    rows = []
    for cid, first, second, want in FOLLOW_UP_CASES:
        conv = sw.StepwiseConversation(session)
        conv.ask(first)
        a = conv.ask(second)
        got = _verdict(a)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _ok(got, want)})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "rows": rows}


# ---------------------------------------------------------------------------
# the scripts (mark T5)
# ---------------------------------------------------------------------------

def answered_chains(session) -> List[Tuple[str, object]]:
    """Every answered chain of the round-two corpus, with its case id."""
    from ..evaluation import stepwise_two_cases as C
    out = []
    for cid, q, *_ in (C.FRAME_CASES + C.UNIT_CASES + C.REGISTER_CASES
                       + C.NARRATIVE_CASES):
        a = sw.answer(session, q)
        if a.answered:
            out.append((cid, a.chain))
    for cid, first, second, _ in C.FOLLOW_UP_CASES:
        conv = sw.StepwiseConversation(session)
        conv.ask(first)
        a = conv.ask(second)
        if a.answered:
            out.append((cid, a.chain))
    return out


def scripts_report(session, limit: Optional[int] = None) -> Dict[str, object]:
    """Every answered chain's column-3 script in a fresh ``python3 -I``, and
    every mutation of each (``limit`` samples the first few chains)."""
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
# non-interference (mark T6)
# ---------------------------------------------------------------------------

def interference_report(session) -> Dict[str, object]:
    """Round one's corpus through the round-two module (marks S1, S2, S4,
    S7 of the round-one study re-taken, S3's controls too), and the router's
    declared sets (S6 re-taken)."""
    one = {
        "composition": sw.composition_report(session),
        "goals": sw.goals_report(session),
        "narratives": sw.narratives_report(session),
        "follow_ups": sw.follow_ups_report(session),
    }
    controls = sw.controls_report(session)
    router = sw.interference_report(session)
    held = (one["composition"]["met"] == one["composition"]["cases"]
            and one["goals"]["met"] == one["goals"]["cases"]
            and one["narratives"]["met"] == one["narratives"]["cases"]
            and one["follow_ups"]["met"] == one["follow_ups"]["cases"]
            and controls["first_found_answers_refused"] >= 3
            and controls["naive_answers_ambiguous"] >= 1)
    return {"round_one": {k: {"cases": v["cases"], "met": v["met"]}
                          for k, v in one.items()},
            "round_one_controls": {
                "first_found_answers_refused":
                    controls["first_found_answers_refused"],
                "naive_answers_ambiguous":
                    controls["naive_answers_ambiguous"]},
            "round_one_held": held,
            "router_read": router["read"],
            "router_questions": router["questions"],
            "turned_into_answers": router["turned_into_answers"],
            "declared_refusals_answered":
                router["declared_refusals_answered"]}


def stepwise_two_report(scripts: bool = True) -> Dict[str, object]:
    """The whole measurement of ``studies/STEPWISE_TWO_STUDY.md``."""
    from .session import GeometricSession
    session = GeometricSession()
    report: Dict[str, object] = {
        "frames": frames_report(session),
        "units": units_report(session),
        "register": register_report(session),
        "controls": controls_report(session),
        "narratives": narratives_report(session),
        "follow_ups": follow_ups_report(session),
        "interference": interference_report(session),
        "study": "studies/STEPWISE_TWO_STUDY.md",
        "lean_file": "RequestProject/GLM/StepwiseFrames.lean",
    }
    if scripts:
        report["scripts"] = scripts_report(session)
    return report
