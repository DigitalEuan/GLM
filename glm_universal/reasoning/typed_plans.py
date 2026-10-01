"""``glm_universal.reasoning.typed_plans`` -- what the typed planner is worth,
measured on questions it was not written from.

What this measures
------------------
:mod:`glm_universal.runtime.semantic_plan` reads a question into typed plans
over operations the session already has and answers only when the licensed
plans agree.  This module asks every question of five sets twice -- through
:meth:`GeometricSession.ask` (the bare grammar) and through the planner -- and
scores both by the same rule
(:func:`glm_universal.evaluation.heldout.score_answer`):

* ``probe-canonical`` and ``probe-paraphrase`` -- the twenty frozen probe
  questions of :mod:`glm_universal.reasoning.blockers` and their paraphrases,
  with the one question whose right outcome is a refusal scored as such;
* ``paraphrases``, ``compositions``, ``adversarial`` -- the held-out sets of
  :mod:`glm_universal.evaluation.heldout`, committed before the planner
  existed;
* ``stress`` -- the hostile set written after the planner's first cut and
  committed before it was run.  Its first-run figures are frozen below in
  :data:`STRESS_FIRST_RUN`, because every change after that run was made
  knowing its result.

The frozen probe is also scored exactly as the blockers study scores it
(:func:`glm_universal.reasoning.blockers._score_asking`, where a refusal is a
refusal even when it is the right outcome), so the pass mark declared in that
study can be read off directly.

Every answer the planner gains over the grammar is classified as ``table``,
``address`` or ``derive`` by the faculty of the plan that licensed it, as
directive D15 requires: a field read is ``table``; an inverse relation found
by value is ``address``; an exact computation, a comparison, a fold or a
dimensional check is ``derive``.

Exact and float-free.  The figures are cached beside the digest of the
sources they were taken from (:func:`current`), and re-taken with
``python3 -m glm_universal.tools plans --write``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

from .. import integrity

__all__ = [
    "SET_ORDER", "STRESS_FIRST_RUN", "PREREGISTRATION", "sets",
    "plans_report", "module_digest", "measure", "write_measurements",
    "measurements", "state", "current",
]


#: The sets in the order they are reported.
SET_ORDER: Tuple[str, ...] = (
    "probe-canonical", "probe-paraphrase", "paraphrases", "compositions",
    "adversarial", "stress",
)

#: The commits that pre-registered each set, before it was first run.
PREREGISTRATION: Mapping[str, str] = {
    "paraphrases": "8064795",
    "compositions": "8064795",
    "adversarial": "8064795",
    "stress": "ca257db",
}

#: The stress set's first run through the planner, frozen: the planner as it
#: stood when the set was committed.  Later figures were taken after changes
#: made knowing this run, and are reported beside it, never in its place.
STRESS_FIRST_RUN: Mapping[str, int] = {
    "correct": 28, "wrong": 0, "refused": 13, "correct-refusal": 6,
}


def sets() -> Dict[str, Tuple[object, ...]]:
    """Every set, as :class:`~glm_universal.evaluation.heldout.HeldOut`."""
    from ..evaluation.heldout import ALL_SETS, HeldOut
    from .blockers import PROBE
    refuse = {"nl-unknown"}

    def probe(which: str) -> Tuple[object, ...]:
        return tuple(
            HeldOut(q.key, getattr(q, which),
                    None if q.key in refuse else (q.expect.lower(),),
                    q.key, q.why)
            for q in PROBE)

    out: Dict[str, Tuple[object, ...]] = {
        "probe-canonical": probe("question"),
        "probe-paraphrase": probe("paraphrase"),
    }
    out.update(ALL_SETS)
    return out


def _haystack(solution) -> str:
    return " ".join([solution.answer or ""] + [
        f"{key}={value}" for key, value in solution.expected.items()])


_VERDICTS = ("correct", "wrong", "refused", "correct-refusal")


def plans_report(session=None) -> Dict[str, object]:
    """Both paths over every set, and what the planner moved."""
    from ..evaluation.heldout import score_answer
    from ..runtime import semantic_plan as sp
    from .blockers import PASS_MARK, PROBE, _score_asking, run_probe
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()

    rows: List[Dict[str, object]] = []
    tallies: Dict[str, Dict[str, Dict[str, int]]] = {}
    census = {"candidates": 0, "licensed": 0, "unlicensed": 0,
              "answered": 0, "ambiguous": 0, "refused": 0,
              "fallthrough": 0}
    gains = {"table": 0, "address": 0, "derive": 0}
    frames_used: Dict[str, int] = {}
    for name, items in sets().items():
        tally = {"bare": dict.fromkeys(_VERDICTS, 0),
                 "planned": dict.fromkeys(_VERDICTS, 0)}
        for item in items:
            bare = session.ask(item.question)                  # type: ignore[attr-defined]
            planned_view = sp.plan_question(session, item.question)  # type: ignore[attr-defined]
            planned = sp.ask_planned(session, item.question)   # type: ignore[attr-defined]
            vb = score_answer(item, bare.ok, _haystack(bare))  # type: ignore[arg-type]
            vp = score_answer(item, planned.ok, _haystack(planned))  # type: ignore[arg-type]
            tally["bare"][vb] += 1
            tally["planned"][vp] += 1
            census["candidates"] += len(planned_view.outcomes)
            census["licensed"] += sum(1 for o in planned_view.outcomes
                                      if o.licensed)
            census["unlicensed"] += sum(1 for o in planned_view.outcomes
                                        if not o.licensed)
            census[planned_view.verdict] += 1
            chosen = planned_view.chosen
            faculty = chosen.faculty if chosen is not None else ""
            frame = chosen.plan.frame if chosen is not None else ""
            if frame:
                frames_used[frame] = frames_used.get(frame, 0) + 1
            gained = vp == "correct" and vb != "correct"
            if gained and planned_view.verdict == "answered":
                gains[faculty] += 1
            rows.append({
                "set": name, "key": item.key,                  # type: ignore[attr-defined]
                "question": item.question,                     # type: ignore[attr-defined]
                "expect": list(item.expect) if item.expect else None,  # type: ignore[attr-defined]
                "bare": vb, "planned": vp,
                "verdict": planned_view.verdict,
                "frame": frame, "faculty": faculty,
                "plan": (chosen.plan.query or chosen.plan.compute)
                if chosen is not None else "",
                "reason": planned_view.reason[:300],
                "answer": (planned.answer or planned.error or "")[:300],
                "gained": gained,
            })
        tallies[name] = tally

    class _Planned:
        def ask(self, text: str):
            return sp.ask_planned(session, text)

    probe_rows = [_score_asking(_Planned(), q.question, q.expect)
                  for q in PROBE]
    frozen = {v: sum(1 for r in probe_rows if r["verdict"] == v)
              for v in ("correct", "wrong", "refused")}
    passed = (frozen["correct"] >= PASS_MARK["correct_at_least"]
              and frozen["wrong"] <= PASS_MARK["wrong_at_most"])

    bare_probe = dict(run_probe()["canonical"])              # type: ignore[arg-type]
    held = ("paraphrases", "compositions", "adversarial")
    held_planned = {v: sum(tallies[s]["planned"][v] for s in held)
                    for v in _VERDICTS}
    held_bare = {v: sum(tallies[s]["bare"][v] for s in held)
                 for v in _VERDICTS}
    held_total = sum(held_planned.values())
    wrong_total = sum(tallies[s]["planned"]["wrong"] for s in tallies)
    wrong_rows = tuple(r for r in rows if r["planned"] == "wrong")
    ambiguous_rows = tuple(r for r in rows if r["verdict"] == "ambiguous")
    return {
        "sets": SET_ORDER,
        "tallies": tallies,
        "rows": tuple(rows),
        "questions": len(rows),
        "held_total": held_total,
        "held_planned": held_planned,
        "held_bare": held_bare,
        "held_safe_coverage": f"{held_planned['correct'] + held_planned['correct-refusal']}"
                              f"/{held_total}",
        "frozen_probe": frozen,
        "frozen_probe_bare": bare_probe,
        "pass_mark": dict(PASS_MARK),
        "probe_passed": passed,
        "census": census,
        "gains": gains,
        "gained_total": sum(gains.values()),
        "frames": len(sp.FRAMES),
        "frames_used": dict(sorted(frames_used.items())),
        "units": len(sp.UNITS),
        "wrong_total": wrong_total,
        "wrong_rows": wrong_rows,
        "ambiguous_rows": ambiguous_rows,
        "stress_first_run": dict(STRESS_FIRST_RUN),
        "preregistration": dict(PREREGISTRATION),
        "verdict": (
            f"through the planner the frozen probe scores "
            f"{frozen['correct']} correct, {frozen['wrong']} wrong and "
            f"{frozen['refused']} refused of {len(PROBE)} against the "
            f"grammar's {bare_probe['correct']}, {bare_probe['wrong']} and "
            f"{bare_probe['refused']}, and {'passes' if passed else 'fails'} the mark declared before the "
            f"probe was first run; on the {held_total} held-out questions "
            f"committed before the planner existed it gives "
            f"{held_planned['correct']} correct answers and "
            f"{held_planned['correct-refusal']} correct refusals with "
            f"{held_planned['wrong']} wrong, against "
            f"{held_bare['correct']}, {held_bare['correct-refusal']} and "
            f"{held_bare['wrong']} through the grammar."),
        "caveat": (
            "the held-out sets were written by the same author as the "
            "frames, an hour before them, so they measure phrasing the "
            "author anticipated as well as phrasing he did not; the stress "
            "set was written knowing the frames and is evidence of safety "
            "rather than of reach. Every gained answer is an operation the "
            "system already had, reached from English: the table gains are "
            "coverage, not reasoning."),
    }


# ===========================================================================
#  THE CACHE, GUARDED BY A DIGEST
# ===========================================================================

DATA_PATH = Path(__file__).resolve().parent / "_data" / "typed_plans.json"

_SOURCES: Tuple[str, ...] = (
    "reasoning/typed_plans.py",
    "runtime/semantic_plan.py",
    "evaluation/heldout.py",
    "runtime/fields.py",
    "runtime/parser.py",
    "runtime/session.py",
    "reasoning/coordinate_order.py",
    "reasoning/column_extremum.py",
    "reasoning/scale_conversion.py",
    "reasoning/blockers.py",
)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def measure() -> Dict[str, object]:
    """The whole study, recomputed."""
    payload = dict(plans_report())
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(measure(), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n",
                      encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = loaded if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the sources as they stand?"""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The measurements if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored


if __name__ == "__main__":                      # pragma: no cover
    print(f"wrote {write_measurements()}")
    print(f"digest {module_digest()}")
