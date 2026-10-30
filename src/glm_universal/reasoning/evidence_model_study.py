"""``glm_universal.reasoning.evidence_model_study`` -- the marks of
``studies/EVIDENCE_MODEL_STUDY.md`` (Phase 169).

*Created 20 October 2026.  Last altered 20 October 2026 (Phase 174: the
census records the stored measurements its answers quote, ``quoted``, and
its digest covers them -- ``studies/QUOTED_MEASUREMENTS_STUDY.md``).*

Every question of the end-to-end evaluation is routed as the command line
routes it (``runtime.router.route``) and read into the common result model
(``runtime.evidence.Result``), with column 3 replayed where the answer has
one.  The census says, field by field and surface by surface, what the model
exposes; the marks say whether it exposes it truthfully.  The corpus and the
conversation are read through their own adapters (``from_define``,
``from_turn``).

Exactness: strings and integers only.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity
from .. import quoted_measurements as qm

__all__ = ["DATA_PATH", "DEFINE_TERMS", "TIE_SCRIPT", "case_result",
           "compute", "measure", "write_measurements", "measurements",
           "state", "current", "evidence_model_report"]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "evidence_model_study.json"

#: The corpus terms read through ``from_define`` (R8).
DEFINE_TERMS: Tuple[str, ...] = ("golay code", "leech lattice", "tier 0",
                                 "register", "yalog")

#: A conversation read through ``from_turn`` (R8): a tie, then its reply.
TIE_SCRIPT: Tuple[str, ...] = ("nearest to albedo moved 4 by 1/4", "no")
TIE_HEAD: Tuple[str, ...] = ("physics:absorptance", "physics:albedo")

_SOURCES: Tuple[str, ...] = (
    "reasoning/evidence_model_study.py",
    "runtime/evidence.py",
    "runtime/router.py",
    "runtime/session.py",
    "runtime/conversation.py",
    "runtime/tct_engine.py",
    "evaluation/cases.py",
    "evaluation/harness.py",
)

#: The caches downstream of this one, never counted as quoted: the Phase 171
#: census digests this file, so counting it here would make a cycle.
_DOWNSTREAM: Tuple[Path, ...] = (_HERE / "_data" / "evidence_in_use_study.json",)

_SESSION = None


def case_result(question: str) -> Dict[str, object]:
    """One evaluation question, routed and read into the model, column 3
    replayed; the stored measurements it read are kept under ``_quoted``
    (Phase 174)."""
    with qm.recording() as seen:
        row = _case_result(question)
    row["_quoted"] = sorted(seen)
    return row


def _case_result(question: str) -> Dict[str, object]:
    global _SESSION
    from ..runtime import evidence as evm
    from ..runtime import router
    from ..runtime.session import GeometricSession
    if _SESSION is None:
        _SESSION = GeometricSession()
    try:
        routed = router.route(_SESSION, question)
        r = evm.from_routed(question, routed, replay=True)
    except Exception as error:                     # pragma: no cover
        return {"question": question, "error": repr(error)}
    d = r.as_dict()
    d["ok_flag"] = bool(routed.answered)
    return d


def _jobs() -> int:
    return max(1, min(8, int(os.environ.get("GLM_EVIDENCE_JOBS",
                                            os.cpu_count() or 1))))


def _adapters() -> Dict[str, object]:
    from ..runtime import evidence as evm
    from ..runtime.conversation import Conversation
    from ..runtime.session import GeometricSession
    from ..knowledge import model as mdl
    knowledge = mdl.load()
    defines = [evm.from_define(t, knowledge).as_dict() for t in DEFINE_TERMS]
    conv = Conversation(session=GeometricSession(domains=()))
    turns = []
    for text in TIE_SCRIPT:
        conv.ask(text)
        turns.append(evm.from_turn(conv.turns[-1]).as_dict())
    return {"define": defines, "turns": turns}


def compute() -> Dict[str, object]:
    with qm.recording() as seen:
        report = _compute()
    quoted = set(seen)
    for r in report["rows"]:
        quoted.update(r.pop("_quoted", ()))
    report["quoted"] = qm.quoted_paths(quoted, (DATA_PATH,) + _DOWNSTREAM)
    return report


def _compute() -> Dict[str, object]:
    from ..evaluation import cases as ev
    from ..runtime import evidence as evm
    cases = list(ev.CASES)
    questions = [c.question for c in cases]
    if _jobs() > 1:
        with ProcessPoolExecutor(max_workers=_jobs()) as pool:
            rows = list(pool.map(case_result, questions))
    else:
        rows = [case_result(q) for q in questions]
    for c, r in zip(cases, rows):
        r["id"], r["expect"] = c.id, c.expect
    good = [r for r in rows if "error" not in r]
    answered = [r for r in good if r["status"] in ("answered", "open")]
    refused = [r for r in good if r["status"] in ("refused", "contradicted")]
    disagree = [r["id"] for r in good
                if (r["status"] in ("answered", "open"))
                != (r["expect"] == "answer")]
    flag_disagree = [r["id"] for r in good
                     if r["ok_flag"] != (r["expect"] == "answer")]
    cited = sorted({t for r in good for t in r["theorems"]})
    undeclared = sorted({t for r in good for t in r["theorems"]
                         if t not in r["theorems_declared"]})
    replayable = [r for r in answered if r["replayed"] is not None]
    replay_failed = [r["id"] for r in replayable if not r["replayed"]]
    opened = [r for r in good if r["status"] == "open"]
    with_given = [r for r in good if r["history"]]
    history_ok = sum(1 for r in with_given
                     if len(r["history"]) == r["question"].count(" is "))
    fields_ok = sum(1 for r in good if all(f in r for f in evm.FIELDS))
    adapters = _adapters()
    defines = adapters["define"]
    turns = adapters["turns"]
    census = {
        "by_surface": dict(sorted(Counter(r["surface"] for r in good)
                                  .items())),
        "by_status": dict(sorted(Counter(r["status"] for r in good).items())),
        "by_evidence": dict(sorted(Counter(r["evidence"][0] for r in good)
                                   .items())),
        "by_boundary": dict(sorted(Counter(r["boundary"] for r in good)
                                   .items())),
        "with_candidates": sum(1 for r in good if r["candidates"]),
        "with_theorems": sum(1 for r in good if r["theorems"]),
        "with_witness": sum(1 for r in good if r["witness"]),
        "steps": sum(r["budget"].get("steps", 0) for r in good),
    }
    report = {
        "cases": len(rows), "errors": [r for r in rows if "error" in r],
        "census": census,
        "R2": {"disagree": disagree, "ok_flag_disagree": flag_disagree},
        "R3": {"refused": len(refused),
               "with_reason": sum(1 for r in refused if r["refusal"])},
        "R4": {"answered": len(answered),
               "unclassified": [r["id"] for r in answered
                                if r["evidence"][0] == "unclassified"]},
        "R5": {"cited": cited, "undeclared": undeclared},
        "R6": {"answered": len(answered), "replayable": len(replayable),
               "verified": len(replayable) - len(replay_failed),
               "failed": replay_failed},
        "R7": {"open": len(opened),
               "open_with_candidates": sum(
                   1 for r in opened if r["candidates"] and r["ambiguity"]),
               "with_given": len(with_given), "history_ok": history_ok},
        "R8": {"define": defines, "turns": turns},
        "R9": {"fields_ok": fields_ok, "results": len(good)},
        "rows": rows,
    }
    report["marks"] = _marks(report)
    report["met"] = sum(1 for v in report["marks"].values() if v)
    report["taken"] = len(report["marks"])
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    d = r["R8"]["define"]
    t = r["R8"]["turns"]
    head = set(TIE_HEAD)
    return {
        "R1": not r["errors"] and r["cases"] > 0,
        "R2": not r["R2"]["disagree"],
        "R3": r["R3"]["with_reason"] == r["R3"]["refused"],
        "R4": not r["R4"]["unclassified"],
        "R5": not r["R5"]["undeclared"],
        "R6": not r["R6"]["failed"] and r["R6"]["replayable"] > 0,
        "R7": r["R7"]["open"] > 0
        and r["R7"]["open_with_candidates"] == r["R7"]["open"]
        and r["R7"]["history_ok"] == r["R7"]["with_given"] > 0,
        "R8": all(x["status"] == "answered" and x["witness"]
                  and x["boundary"].startswith("corpus:") for x in d[:-1])
        and d[-1]["status"] == "refused" and bool(d[-1]["refusal"])
        and t[0]["status"] == "open" and set(t[0]["candidates"]) <= head
        and len(t[1]["history"]) == 1
        and set(t[1]["candidates"]) <= head,
        "R9": r["R9"]["fields_ok"] == r["R9"]["results"],
    }


def module_digest(quoted: Optional[List[str]] = None) -> str:
    """The digest of the sources and, since Phase 174, of the stored
    measurements the census's answers quoted (``quoted``, as recorded; by
    default the stored measurement's own list)."""
    root = Path(__file__).resolve().parent.parent
    if quoted is None:
        stored = measurements()
        quoted = list((stored or {}).get("quoted", ()))
    names = [root / n for n in sorted(set(_SOURCES))]
    names += [p for p in qm.existing(quoted) if p not in names]
    return integrity.tree_digest(names, root)


def measure() -> Dict[str, object]:
    report = compute()
    report["source_digest"] = module_digest(report["quoted"])
    return report


def write_measurements(path: Optional[Path] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.write_text(json.dumps(measure(), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    fresh = stored.get("source_digest") == live
    return {"present": True, "fresh": fresh,
            "verdict": "current" if fresh else "stale",
            "live_digest": live, "stored_digest": stored.get("source_digest")}


def current() -> Optional[Dict[str, object]]:
    return measurements() if state()["fresh"] else None


def evidence_model_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools evidence-model --write")}
    return dict(stored, available=True)
