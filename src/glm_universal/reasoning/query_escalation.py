"""``glm_universal.reasoning.query_escalation`` -- what the escalation loop
costs and what it buys, measured over declared sets.

The loop itself is :mod:`glm_universal.runtime.escalation_loop`; this module is
its measurement, and it is pre-registered in
``studies/QUERY_ESCALATION_STUDY.md``.

Three questions, in the order they matter
-----------------------------------------
**Safety.**  Does wiring escalation into the query loop change any answer the
runtime already gives, and does it ever convert a *principled* refusal --
ill formed, underdetermined, or grounded in no register -- into an answer?  The
whole evaluation set is run both ways and compared, and the gate is that the
answered cases are answered identically at the first rung, at the first rung's
cost, and that no case classified principled is answered at any rung.

**Utility.**  Does any refusal actually resolve above the first rung?  A loop
with no instance is machinery, not a faculty.  The probe set below is declared
in the study before it was run, and the count of probes that resolve above L1
is the reading.

**Cost.**  What does an escalated answer cost against a direct one?  Every rung
run is charged, so an answer reached at L3 is reported as more expensive than
one reached at L1 and the runtime cannot quietly buy accuracy with work.

Exactness
---------
Integers only: rung costs, counts and edit distances.  No float, no random
source and no digest beyond the cache guard.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity
from ..runtime import escalation_loop as esl

__all__ = [
    "PROBES", "probe_rows", "evaluation_rows", "safety", "utility",
    "classification_rows", "query_escalation_report",
    "module_digest", "measure", "write_measurements", "measurements",
    "state", "current", "DATA_PATH",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE DECLARED PROBE SET
# ═════════════════════════════════════════════════════════════════════════

#: ``(query, what it is here to test)``.  Declared in the study before the
#: loop was run against it, and reported in full whatever each one does.  The
#: set deliberately contains probes of every outcome the loop can produce,
#: including ones expected to stay refused: a probe set of things that work is
#: not a measurement.
PROBES: Tuple[Tuple[str, str], ...] = (
    ("describe energy",
     "a question the register answers: must be answered at L1, at L1's cost"),
    ("nearest to c",
     "a symbol the register itself spells: L1 again"),
    ("nearest to k_B",
     "a constant the register does not spell but the reference layer "
     "denotes: the semantics rung, or nothing"),
    ("nearest to N_A",
     "the same, for a second constant"),
    ("describe energie",
     "a misspelling one edit outside the index: the neighbourhood rung, or "
     "nothing"),
    ("describe oxigen",
     "the same, in the chemistry register"),
    ("nearest to velocty",
     "the same, for a different query kind"),
    ("describe watter",
     "a misspelling with *two* aliases inside the radius: must refuse, "
     "because a lookup that picks between candidates is guessing"),
    ("describe unobtainium",
     "a word absent from every register: must refuse, and the absence should "
     "be certified within the declared radius"),
    ("describe justice",
     "open vocabulary: must refuse, certified in the same way"),
    ("report nonsense subject",
     "a one-rung ladder: refused at the top of a tower one rung high"),
    ("Ca : Sc :: Ba : ?",
     "underdetermined: the cell holds fifteen elements, so no rung may "
     "answer"),
    ("heat : temperature :: acceleration : ?",
     "ungrounded: the conjugate register has no column for the operand"),
    ("please compute the square root of a banana",
     "ill formed: no rule matched, so there is no question to re-read"),
    ("is 0.1 + 0.2 equal to 0.3",
     "undecidable equality: answered as a refusal in prose, and untouched"),
    ("measure large in room",
     "a word and a class of different quantities: ungrounded at every "
     "layer"),
    ("derive cents of perfect_fifth",
     "a coordinate no description derives: ungrounded at every layer"),
    ("approximate 1/0 to 5 places",
     "ill formed: a quotient by an exact zero names no value"),
)


def _session():
    from ..runtime.session import GeometricSession
    return GeometricSession()


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE PROBES, RUN
# ═════════════════════════════════════════════════════════════════════════

def probe_rows(session=None) -> Tuple[Dict[str, object], ...]:
    """Every declared probe, with the rung it stopped at and what it cost."""
    session = session or _session()
    rows: List[Dict[str, object]] = []
    for question, purpose in PROBES:
        direct = session.ask(question)
        climb = session.escalate(question)
        rows.append({
            "query": question,
            "purpose": purpose,
            "kind": climb.query.kind,
            "ladder": climb.ladder,
            "direct_ok": direct.ok,
            "answered": climb.answered,
            "layer": climb.layer,
            "cost": climb.cost,
            "direct_cost": esl.LAYER_BY_KEY[climb.ladder[0]].cost,
            "escalated": climb.escalated,
            "refusal_tag": climb.refusal_tag,
            "certified_absence": climb.certified_absence,
            "verdict": climb.verdict,
        })
    return tuple(rows)


def evaluation_rows(session=None) -> Tuple[Dict[str, object], ...]:
    """Every evaluation case, run directly and through the loop."""
    from ..evaluation import cases as ev
    session = session or _session()
    rows: List[Dict[str, object]] = []
    for case in ev.CASES:
        try:
            direct = session.ask(case.question)
        except Exception as exc:                # pragma: no cover - defensive
            rows.append({"id": case.id, "kind": case.kind,
                         "expect": case.expect, "raised": str(exc),
                         "comparable": False})
            continue
        climb = session.escalate(case.question)
        rows.append({
            "id": case.id,
            "kind": case.kind,
            "expect": case.expect,
            "direct_ok": direct.ok,
            "direct_answer": direct.answer,
            "answered": climb.answered,
            "answer": climb.solution.answer,
            "layer": climb.layer,
            "cost": climb.cost,
            "escalated": climb.escalated,
            "refusal_tag": climb.refusal_tag,
            "same_answer": (direct.ok == climb.solution.ok
                            and direct.answer == climb.solution.answer),
            "comparable": True,
        })
    return tuple(rows)


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE THREE READINGS
# ═════════════════════════════════════════════════════════════════════════

def safety(rows: Tuple[Dict[str, object], ...]) -> Dict[str, object]:
    """Nothing the runtime already answers may move, and no principled
    refusal may become an answer."""
    answered = [row for row in rows if row.get("direct_ok")]
    moved = [row["id"] for row in answered if not row.get("same_answer")]
    dear = [row["id"] for row in answered
            if row.get("cost") != esl.LAYERS[0].cost]
    converted = [row["id"] for row in rows
                 if row.get("answered")
                 and not row.get("direct_ok")
                 and row.get("refusal_tag") not in (None, esl.ESCALATABLE)]
    return {
        "cases": len(rows),
        "answered_directly": len(answered),
        "answers_moved": tuple(moved),
        "answers_costing_more_than_the_first_rung": tuple(dear),
        "principled_refusals_converted": tuple(converted),
        "holds": not moved and not dear and not converted,
    }


def utility(rows: Tuple[Dict[str, object], ...]) -> Dict[str, object]:
    """What the loop buys: the probes that resolve above the first rung."""
    resolved = [row for row in rows if row.get("answered")
                and row.get("escalated")]
    refused = [row for row in rows if not row.get("answered")]
    certified = [row for row in refused if row.get("certified_absence")]
    by_layer: Dict[str, int] = {}
    for row in rows:
        if row.get("answered"):
            key = str(row["layer"])
            by_layer[key] = by_layer.get(key, 0) + 1
    return {
        "probes": len(rows),
        "answered": sum(1 for row in rows if row.get("answered")),
        "answered_by_layer": by_layer,
        "resolved_above_the_first_rung": tuple(str(row["query"])
                                               for row in resolved),
        "refused": len(refused),
        "certified_absences": tuple(str(row["query"]) for row in certified),
        "has_an_instance": bool(resolved),
        "escalated_cost": tuple(int(row["cost"]) for row in resolved),
        "direct_cost": esl.LAYERS[0].cost,
    }


def classification_rows(session=None) -> Tuple[Dict[str, object], ...]:
    """Every declared refusal of the evaluation set, and how it is classified.

    This is the table the fourth commitment lives or dies by: a refusal
    classified ``absent`` will be escalated, and any other classification stops
    the loop at the layer the refusal was made at.
    """
    from ..evaluation import cases as ev
    session = session or _session()
    rows: List[Dict[str, object]] = []
    for case in ev.CASES:
        if case.expect != "refusal":
            continue
        climb = session.escalate(case.question)
        rows.append({
            "id": case.id,
            "kind": case.kind,
            "query": case.question,
            "answered_as_prose": climb.solution.ok,
            "tag": climb.refusal_tag,
            "escalatable": climb.refusal_tag == esl.ESCALATABLE,
            "layer": climb.layer,
            "cost": climb.cost,
            "answered": climb.answered,
        })
    return tuple(rows)


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def query_escalation_report() -> Dict[str, object]:
    """Everything this round knows, recomputed on call."""
    session = _session()
    probes = probe_rows(session)
    evaluation = evaluation_rows(session)
    classified = classification_rows(session)
    return {
        "layers": tuple({"key": layer.key, "title": layer.title,
                         "cost": layer.cost,
                         "description": layer.description}
                        for layer in esl.LAYERS),
        "ladders": esl.ladder_table(),
        "radius": esl.NEIGHBOURHOOD_RADIUS,
        "markers": len(esl.PRINCIPLED_MARKERS),
        "probes": probes,
        "evaluation": evaluation,
        "classified": classified,
        "safety": safety(evaluation),
        "utility": utility(probes),
        "tallest_ladder": max(len(row["rungs"])            # type: ignore[arg-type]
                              for row in esl.ladder_table()),
        "kinds_with_a_ladder_above_one_rung": sum(
            1 for row in esl.ladder_table() if len(row["rungs"]) > 1),  # type: ignore[arg-type]
        "method": (
            "The loop climbs a ladder declared per query kind, charges every "
            "rung it runs, refuses to escalate a refusal classified as "
            "principled, and reports the layer a refusal was made at.  This "
            "module runs the whole evaluation set both ways to check that "
            "nothing already answered moves, and a declared probe set to see "
            "whether anything is bought."),
        "limits": (
            "The tower is three rungs and covers the query kinds named in "
            "the ladder table; a kind with a one-rung ladder is declared as "
            "such rather than escalated by default.  The classification of a "
            "refusal is by declared marker, so a refusal whose wording "
            "changes is re-classified as an absence and escalated -- which "
            "fails safe towards spending work, not towards answering."),
    }


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = (Path(__file__).resolve().parent / "_data"
             / "query_escalation.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/query_escalation.py",
    "runtime/escalation_loop.py",
    "runtime/session.py",
    "runtime/parser.py",
    "semantics/reference.py",
    "evaluation/cases.py",
)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    """The report, with the digest of what it was taken from beside it."""
    payload = dict(query_escalation_report())
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n", encoding="utf-8")
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
