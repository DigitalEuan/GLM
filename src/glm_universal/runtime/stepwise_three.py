"""``glm_universal.runtime.stepwise_three`` -- the measurement of round three
of the stepwise planner.

``studies/STEPWISE_THREE_STUDY.md`` (Phase 84) declares eight marks over the
corpus of :mod:`glm_universal.evaluation.stepwise_three_cases`; this module
takes the seven that are measured (the eighth is the Lean file).  The frames
themselves live where they run: :mod:`glm_universal.runtime.stepwise` (the
grammar and the steps), :mod:`glm_universal.runtime.declared_frames` (the
declared comparatives, count nouns and sets),
:mod:`glm_universal.runtime.quantity_units` (tera and pico) and
:mod:`glm_universal.reasoning.stepwise_script` (the three columns of the new
steps).

Two controls:

* **Round two's reader** -- the same modules with
  :data:`glm_universal.runtime.stepwise.ROUND_THREE` and
  :data:`glm_universal.runtime.quantity_units.WIDEN` switched off: what the
  corpus met before this round (marks V1-V4).
* **Fold the rows that are present** -- every fold over a column with a
  missing reading answered over the rows that hold one (mark V5).  It is the
  reading the hole rule exists to prevent.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from . import router
from . import stepwise as sw
from . import stepwise_two as s2
from ..reasoning import stepwise_script as ss

__all__ = ["round_two_reader", "comparatives_report", "counts_report",
           "prefixes_report", "folds_report", "present_rows",
           "controls_report", "partition_report", "follow_ups_report",
           "scripts_report", "interference_report", "stepwise_three_report",
           "answered_chains"]


class round_two_reader:
    """The stepwise planner as round two left it: round three switched off.

    Used as ``with round_two_reader(): ...``; both flags are restored."""

    def __enter__(self):
        from . import quantity_units as qu
        self._saved = (sw.ROUND_THREE, qu.WIDEN)
        sw.ROUND_THREE = False
        qu.WIDEN = False
        return self

    def __exit__(self, *exc) -> bool:
        from . import quantity_units as qu
        sw.ROUND_THREE, qu.WIDEN = self._saved
        return False


def _verdict(a) -> Tuple[str, ...]:
    return sw._verdict_of(a)


def _ok(got, want) -> bool:
    return tuple(got[:len(want)]) == tuple(want)


def _rows(session, cases, stitched: bool = False) -> Dict[str, object]:
    rows = []
    for case in cases:
        cid, q, want = case[0], case[1], case[2]
        a = sw.answer(session, q)
        with round_two_reader():
            before = sw.answer(session, q)
            routed_before = router.route(session, q)
        routed = router.route(session, q)
        got = _verdict(a)
        from .frame_declarations import declared_verdict
        want = declared_verdict("stepwise_three", cid, want)
        ok = _ok(got, want)
        row = {"id": cid, "want": list(want), "got": list(got),
               "round_two": list(_verdict(before)),
               "machine_before": routed_before.text if
               routed_before.answered else None,
               "machine_now": routed.text if routed.answered else None,
               "machine_by": getattr(routed.solution, "kind", None)
               if routed.answered else None}
        moved = tuple(want) != tuple(case[2])
        if stitched and not moved:
            # a case Phase 91 declared moved declares its verdict only
            ok = ok and (not a.answered or sw.stitched_of(a) == case[3])
        if stitched:
            row["stitched"] = list(sw.stitched_of(a))
            row["want_stitched"] = list(case[3])
        row["ok"] = ok
        rows.append(row)
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows
                         if r["got"][0] == "ANSWER" and not r["ok"]),
            "round_two_answers": sum(1 for r in rows
                                     if r["round_two"][0] == "ANSWER"),
            "machine_answered_before": sum(1 for r in rows
                                           if r["machine_before"] is not None),
            "machine_answers_now": sum(1 for r in rows
                                       if r["machine_now"] is not None),
            "rows": rows}


def comparatives_report(session) -> Dict[str, object]:
    """Mark V1: the declared comparatives."""
    from ..evaluation.stepwise_three_cases import COMPARATIVE_CASES
    return _rows(session, COMPARATIVE_CASES)


def counts_report(session) -> Dict[str, object]:
    """Mark V2: the further count nouns."""
    from ..evaluation.stepwise_three_cases import COUNT_CASES
    return _rows(session, COUNT_CASES)


def prefixes_report(session) -> Dict[str, object]:
    """Mark V3: tera and pico."""
    from ..evaluation.stepwise_three_cases import PREFIX_CASES
    return _rows(session, PREFIX_CASES, stitched=True)


def folds_report(session) -> Dict[str, object]:
    """Mark V4: folds over a column."""
    from ..evaluation.stepwise_three_cases import FOLD_CASES
    return _rows(session, FOLD_CASES)


# ---------------------------------------------------------------------------
# the controls (mark V5)
# ---------------------------------------------------------------------------

def present_rows(session, text: str) -> Optional[str]:
    """What *fold the rows that are present* answers to a fold question:
    the fold over the members that hold a reading; None when the question
    is no fold over a declared set."""
    from . import declared_frames as df
    try:
        readings = [t for seg in sw.split_then(text)
                    for t in sw.segment_readings(seg)]
    except sw.Refused:
        return None

    def find(t):
        if not isinstance(t, tuple):
            return None
        if t and t[0] == "fold":
            return t
        for x in t[1:]:
            got = find(x)
            if got is not None:
                return got
        return None

    fold = next((f for f in map(find, readings) if f is not None), None)
    if fold is None:
        return None
    _, fn, key, phrase = fold
    fs = session.field_surface
    field_name = df.resolve_field(fs, phrase)
    if field_name is None:
        return None
    table = fs.table_by_name(df.ELEMENT_TABLE).rows()
    vals = [Fraction(table[k][field_name]) for k, _ in df.members(fs, key)
            if table[k].get(field_name) is not None]
    if not vals:
        return None
    if fn == "sum":
        return ss.render_value(sum(vals, Fraction(0)))
    if fn == "mean":
        return ss.render_value(sum(vals, Fraction(0)) / len(vals))
    want = 1 if fn == "odd" else 0
    return str(sum(1 for v in vals if v.denominator == 1
                   and v.numerator % 2 == want))


def partition_report(session) -> Dict[str, object]:
    """The classes are the column: on every numeric element-table column
    with no missing reading, the sum over all the elements equals the sum
    of the sums over the declared classes."""
    from . import declared_frames as df
    fs = session.field_surface
    table = fs.table_by_name(df.ELEMENT_TABLE).rows()
    classes = [k for k, v in df.DECLARED_SETS.items() if v is not None]
    columns = list(next(iter(table.values())).keys())
    rows = []
    for c in columns:
        vals = [r.get(c) for r in table.values()]
        if any(v is None or isinstance(v, bool)
               or not isinstance(v, (int, Fraction)) for v in vals):
            continue
        whole = sum((Fraction(v) for v in vals), Fraction(0))
        parts = sum((Fraction(table[k][c]) for key in classes
                     for k, _ in df.members(fs, key)), Fraction(0))
        rows.append({"column": c, "whole": ss.render_value(whole),
                     "classes": ss.render_value(parts),
                     "ok": whole == parts})
    covered = sum(len(df.members(fs, key)) for key in classes)
    return {"columns": len(rows), "agree": sum(r["ok"] for r in rows),
            "rows_in_classes": covered, "rows": len(table),
            "met": bool(rows) and all(r["ok"] for r in rows)
            and covered == len(table), "detail": rows}


def controls_report(session) -> Dict[str, object]:
    """Mark V5: the present-rows control on the declared holes, and the
    partition of the column by the declared classes."""
    from ..evaluation.stepwise_three_cases import (FOLD_CASES,
                                                   HOLE_CONTROL_AT_LEAST)
    holes = [(cid, q) for cid, q, want in FOLD_CASES
             if tuple(want) == ("REFUSED", "COLUMN_HOLE")]
    rows = [{"id": cid, "present_rows": present_rows(session, q)}
            for cid, q in holes]
    answered = [r["id"] for r in rows if r["present_rows"] is not None]
    part = partition_report(session)
    return {"holes": len(rows), "present_rows_answers": answered,
            "at_least": HOLE_CONTROL_AT_LEAST, "rows": rows,
            "partition": part,
            "met": len(answered) >= HOLE_CONTROL_AT_LEAST and part["met"]}


def follow_ups_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_three_cases import FOLLOW_UP_CASES
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
# the scripts (mark V6)
# ---------------------------------------------------------------------------

def answered_chains(session) -> List[Tuple[str, object]]:
    """Every answered chain of the round-three corpus, with its case id."""
    from ..evaluation import stepwise_three_cases as C
    out = []
    for cid, q, *_ in (C.COMPARATIVE_CASES + C.COUNT_CASES + C.PREFIX_CASES
                       + C.FOLD_CASES):
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
    every mutation of each."""
    import re
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
# non-interference (mark V7)
# ---------------------------------------------------------------------------

def interference_report(session) -> Dict[str, object]:
    """Rounds one and two's corpora through the round-three module (their
    marks re-taken without scripts), and the router's declared sets."""
    two = {
        "frames": s2.frames_report(session),
        "units": s2.units_report(session),
        "register": s2.register_report(session),
        "narratives": s2.narratives_report(session),
        "follow_ups": s2.follow_ups_report(session),
    }
    two_controls = s2.controls_report(session)
    one = s2.interference_report(session)
    held_two = all(v["met"] == v["cases"] for v in two.values()) and \
        two["frames"]["round_one_answers"] == 0 and two_controls["met"]
    return {"round_two": {k: {"cases": v["cases"], "met": v["met"]}
                          for k, v in two.items()},
            "round_two_controls_met": two_controls["met"],
            "round_two_held": held_two,
            "round_one": one["round_one"],
            "round_one_held": one["round_one_held"],
            "router_read": one["router_read"],
            "router_questions": one["router_questions"],
            "turned_into_answers": one["turned_into_answers"],
            "declared_refusals_answered": one["declared_refusals_answered"]}


def stepwise_three_report(scripts: bool = True) -> Dict[str, object]:
    """The whole measurement of ``studies/STEPWISE_THREE_STUDY.md``."""
    from .session import GeometricSession
    session = GeometricSession()
    report: Dict[str, object] = {
        "comparatives": comparatives_report(session),
        "counts": counts_report(session),
        "prefixes": prefixes_report(session),
        "folds": folds_report(session),
        "controls": controls_report(session),
        "follow_ups": follow_ups_report(session),
        "interference": interference_report(session),
        "study": "studies/STEPWISE_THREE_STUDY.md",
        "lean_file": "RequestProject/GLM/StepwiseWiden.lean",
    }
    if scripts:
        report["scripts"] = scripts_report(session)
    return report
