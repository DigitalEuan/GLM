"""``glm_universal.reasoning.evidence_in_use_study`` -- the marks of
``studies/EVIDENCE_IN_USE_STUDY.md`` (Phase 171).

*Created 20 October 2026.  Last altered 20 October 2026 (Phase 174: the
stored measurements its answers quote are recorded, ``quoted``, and its
digest covers them -- ``studies/QUOTED_MEASUREMENTS_STUDY.md``).*

The command line's ``--result`` reading (``GLM.routed_result``) is taken over
every evaluation question and compared with the Phase 169 census (U1, U2);
the evaluation's replay gate (``evaluation/replay.py``) is run over every
case expected answered (U4, U6) and its rule checked on rows written by hand
(U5); the Lean file's theorems are counted (L1).  U3, the end-to-end
evaluation, is read from a run of ``python3 -m glm_universal.evaluation``
recorded beside the measurement.

Exactness: strings and integers only.
"""

from __future__ import annotations

import json
import os
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity
from .. import quoted_measurements as qm

__all__ = ["DATA_PATH", "LEAN_FILE", "LEAN_THEOREMS", "result_row",
           "hand_rows", "compute", "measure", "write_measurements",
           "measurements", "state", "current", "evidence_in_use_report"]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "evidence_in_use_study.json"

_ROOT = Path(__file__).resolve().parents[3]
LEAN_FILE: Path = (_ROOT / "overlay" / "glm_lean" / "RequestProject" / "GLM"
                   / "EvidenceInUse.lean")

#: The five theorems of the study's §2 (L1).
LEAN_THEOREMS: Tuple[str, ...] = ("gate_sound", "gate_fails_of_failed",
                                  "gate_absent_ok", "gate_append",
                                  "read_keeps_answer")

#: The fields U1 compares with the Phase 169 census.
COMPARED: Tuple[str, ...] = ("status", "surface", "kind", "answer")

#: The declared bound of U6, in seconds.
WALL_BOUND = 15 * 60

_SOURCES: Tuple[str, ...] = (
    "reasoning/evidence_in_use_study.py",
    "reasoning/_data/evidence_model_study.json",
    "evaluation/replay.py",
    "evaluation/cases.py",
    "runtime/evidence.py",
    "runtime/router.py",
    "runtime/tct_engine.py",
)

_SESSION = None


def result_row(question: str) -> Dict[str, object]:
    """One evaluation question through ``GLM.routed_result`` (no replay: the
    replay is the gate's, U4); the stored measurements it read are kept under
    ``_quoted`` (Phase 174)."""
    with qm.recording() as seen:
        row = _result_row(question)
    row["_quoted"] = sorted(seen)
    return row


def _result_row(question: str) -> Dict[str, object]:
    global _SESSION
    import GLM
    from ..runtime.session import GeometricSession
    if _SESSION is None:
        _SESSION = GeometricSession()
    try:
        return GLM.routed_result(_SESSION, question).as_dict()
    except Exception as error:                     # pragma: no cover
        return {"question": question, "error": repr(error)}


def hand_rows() -> Dict[str, List[Dict[str, object]]]:
    """The rows of U5: a passing batch, and the batch with one defect each."""
    base = [{"id": "a", "status": "answered", "replayed": True},
            {"id": "b", "status": "open", "replayed": True}]
    return {
        "clean": base,
        "failed_replay": base + [{"id": "f", "status": "answered",
                                  "replayed": False}],
        "unanswered": base + [{"id": "u", "status": "refused",
                               "replayed": None}],
        "error": base + [{"id": "e", "error": "exit 2: boom"}],
        "absent": base + [{"id": "n", "status": "answered",
                           "replayed": None}],
    }


def _jobs() -> int:
    return max(1, min(8, int(os.environ.get("GLM_EVIDENCE_JOBS",
                                            os.cpu_count() or 1))))


def _lean() -> Dict[str, object]:
    text = LEAN_FILE.read_text(encoding="utf-8") if LEAN_FILE.exists() else ""
    found = [t for t in LEAN_THEOREMS
             if re.search(rf"^theorem {t}\b", text, re.MULTILINE)]
    return {"theorems": found, "declared": len(LEAN_THEOREMS),
            "sorry": len(re.findall(r"\bsorry\b", text))}


def run_evaluation() -> Dict[str, int]:
    """U3: the end-to-end evaluation, run as its command runs it."""
    from ..evaluation import harness
    report = harness.evaluation_report(jobs=_jobs())
    return {"cases": int(report["cases"]), "passed": int(report["passed"])}


def compute(evaluation: Optional[Dict[str, int]] = None
            ) -> Dict[str, object]:
    if evaluation is None:
        evaluation = run_evaluation()
    from ..evaluation import cases as ev
    from ..evaluation import replay as rp
    from ..runtime import evidence as evm
    from . import evidence_model_study as ems
    cases = list(ev.CASES)
    questions = [c.question for c in cases]
    if _jobs() > 1:
        with ProcessPoolExecutor(max_workers=_jobs()) as pool:
            rows = list(pool.map(result_row, questions))
    else:
        rows = [result_row(q) for q in questions]
    quoted = qm.quoted_paths({n for r in rows for n in r.pop("_quoted", ())},
                             (DATA_PATH,))
    census = {r["question"]: r for r in (ems.measurements() or {})
              .get("rows", [])}
    agree, disagree = 0, []
    fields_ok = 0
    for c, r in zip(cases, rows):
        if "error" in r:
            disagree.append({"id": c.id, "error": r["error"]})
            continue
        if all(k in r for k in evm.FIELDS):
            fields_ok += 1
        old = census.get(c.question)
        diff = [k for k in COMPARED if old is None or old.get(k) != r.get(k)]
        if diff:
            disagree.append({"id": c.id, "fields": diff})
        else:
            agree += 1
    gate = rp.replay_gate(ev.CASES, jobs=_jobs())
    hand = {name: rp.gate_passes(rp.summarise(rs))
            for name, rs in hand_rows().items()}
    report: Dict[str, object] = {
        "cases": len(cases),
        "quoted": quoted,
        "lean": _lean(),
        "U1": {"agree": agree, "disagree": disagree,
               "census_rows": len(census)},
        "U2": {"fields_ok": fields_ok, "results": len(rows)},
        "U3": evaluation or {},
        "U4": {k: gate[k] for k in ("cases", "replayable", "verified",
                                    "failed", "unreplayable",
                                    "status_disagree", "errors")},
        "U5": hand,
        "U6": {"seconds": gate["seconds"], "bound": WALL_BOUND,
               "jobs": _jobs()},
    }
    report["marks"] = _marks(report)
    report["met"] = sum(1 for v in report["marks"].values() if v)
    report["taken"] = len(report["marks"])
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    lean = r["lean"]
    u4 = r["U4"]
    u3 = r["U3"]
    h = r["U5"]
    return {
        "L1": len(lean["theorems"]) == lean["declared"]
        and lean["sorry"] == 0,
        "U1": r["U1"]["agree"] == r["cases"],
        "U2": r["U2"]["fields_ok"] == r["U2"]["results"] == r["cases"],
        "U3": bool(u3) and u3.get("passed") == u3.get("cases") == r["cases"],
        "U4": u4["replayable"] >= 171 and u4["verified"] == u4["replayable"]
        and not u4["status_disagree"] and not u4["errors"],
        "U5": h["clean"] and h["absent"] and not h["failed_replay"]
        and not h["unanswered"] and not h["error"],
        "U6": r["U6"]["seconds"] <= r["U6"]["bound"],
    }


def module_digest(quoted: Optional[List[str]] = None) -> str:
    """The digest of the sources, ``GLM.py`` and, since Phase 174, the stored
    measurements the answers quoted (by default the stored list)."""
    root = Path(__file__).resolve().parent.parent
    if quoted is None:
        quoted = list((measurements() or {}).get("quoted", ()))
    names = [root / n for n in sorted(set(_SOURCES))]
    names.append(root.parent / "GLM.py")
    names += [p for p in qm.existing(quoted) if p not in names]
    return integrity.tree_digest(names, root.parent)


def measure(evaluation: Optional[Dict[str, int]] = None
            ) -> Dict[str, object]:
    report = compute(evaluation)
    report["source_digest"] = module_digest(report["quoted"])
    return report


def write_measurements(path: Optional[Path] = None,
                       evaluation: Optional[Dict[str, int]] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.write_text(json.dumps(measure(evaluation), indent=1,
                                 sort_keys=True, ensure_ascii=False) + "\n",
                      encoding="utf-8")
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


def evidence_in_use_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools evidence-in-use --write")}
    return dict(stored, available=True)
