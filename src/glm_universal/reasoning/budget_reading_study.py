"""``glm_universal.reasoning.budget_reading_study`` -- the measurement of
Phase 147, the budget rule in the answering path.

``studies/BUDGET_READING_STUDY.md`` pre-registered the marks; this module
takes them.

* **H1-H4** -- the 256 held-out walks of Phase 124 (walk indices
  3000 ... 3255), each walk's hole read twice from the same walk: by the walk's
  own frozen reading (200 starts, patience 40) and under the rule
  (:func:`hole_reading.walked`); and the rule's types against Phase 124's
  stored readings of the same centres.
* **R1** -- ``report deep holes`` under the rule against the same census read
  with the frozen parameters.
* **Q1** -- the question battery of the ``hole`` kind through the session,
  with column 3 and two mutants of every answered claim.
* **W1** -- the wiring census, and no earlier evaluation case read as
  ``hole``.
* **F1** -- the frozen path, from :mod:`budget_guard_frozen`.

The walks take about ten minutes on eight cores, so the measurement is stored
beside the digest of its sources (``tools budget-reading --write``).

Exactness
---------
Integers, strings and :class:`fractions.Fraction` only.
"""

from __future__ import annotations

import dataclasses
import json
import multiprocessing
import os
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity
from . import budget_guard_frozen as bgf
from . import deep_hole_classifier as dhc
from . import deep_holes as dh
from . import hole_reading as hr

__all__ = [
    "HELDOUT_INDICES", "BATTERY", "heldout_row", "heldout_rows",
    "census_comparison", "battery", "wiring", "compute", "budget_reading_report",
    "measure", "write_measurements", "measurements", "state", "current",
    "DATA_PATH",
]

#: Phase 124's held-out walks.
HELDOUT_INDICES: Tuple[int, ...] = tuple(range(3000, 3256))

#: The question battery: ``(id, question, declared)`` where ``declared`` is
#: ``("answered", type)``, ``("refused", reason)`` or ``("read", None)``.
BATTERY: Tuple[Tuple[str, str, tuple], ...] = (
    ("R1", "hole walk x", ("refused", "malformed")),
    ("R2", "hole 1, 2, 3", ("refused", "dimension")),
    ("R3", "hole " + ", ".join(["0"] * 24), ("refused", "lattice-point")),
    ("R4", "hole " + ", ".join(["1/8"] * 23 + ["3/8"]),
     ("refused", "shallow")),
    ("R5", "hole the moon", ("refused", "malformed")),
    ("B1", "hole walk 0", ("answered", "E_8^3")),
    ("B2", "hole walk 1", ("answered", "D_24")),
    ("B3", "hole walk 2", ("answered", "A_12^2")),
    ("B4", "hole octad pair", ("answered", "A_1^24")),
    ("B5", "hole dodecad triangle", ("answered", "A_2^12")),
    ("B6", "hole walk 3006", ("answered", "D_16 E_8")),
    ("B7", "deep hole of walk 3013", ("read", None)),
    ("B8", "hole walk 3067", ("read", None)),
)

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "budget_reading_study.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/budget_reading_study.py", "reasoning/hole_reading.py",
    "reasoning/deep_holes.py", "reasoning/voronoi_walk.py",
    "reasoning/fwht_decode.py", "reasoning/niemeier.py",
    "runtime/session.py", "runtime/parser.py", "runtime/tct_engine.py",
    "runtime/toolbox.py", "runtime/reports/lattice_geometry.py",
)


def _vertex_digest(vertices) -> str:
    canon = sorted(tuple(int(x) for x in v) for v in vertices)
    return integrity.sha256_hex(json.dumps(canon).encode("utf-8"))[:16]


def _summary(classified: Dict[str, object]) -> Dict[str, object]:
    probe = classified["probe"]
    return {"certified": bool(classified["certified"]),
            "type": classified["niemeier_type"] if classified["certified"]
            else None,
            "starts": int(probe.get("starts_run") or 0),
            "vertex_count": int(probe["vertex_count"]),
            "vertices": _vertex_digest(probe["vertices"])}


def heldout_row(index: int) -> Dict[str, object]:
    """One held-out walk: the frozen reading and the rule, from one walk."""
    from . import voronoi_walk
    seed = hr.walk_seed(index)
    reached = voronoi_walk.walk_to_deep_hole(seed=seed)
    row: Dict[str, object] = {"index": index, "seed": seed,
                              "reached": bool(reached and reached["is_deep"])}
    if not row["reached"]:
        return row
    centre, known = reached["center"], reached["active"]
    frozen = dh.classify_carrier(centre, probes=dhc.WALK_PROBES, seed=seed,
                                 patience=dhc.WALK_PATIENCE, known=known)
    rule = dh.classify_carrier(centre, probes=hr.BUDGET, seed=seed,
                               patience=hr.BUDGET, known=known)
    row["frozen"] = _summary(frozen)
    row["rule"] = _summary(rule)
    return row


def heldout_rows(jobs: Optional[int] = None) -> List[Dict[str, object]]:
    jobs = jobs or os.cpu_count() or 1
    if jobs > 1:
        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(jobs) as pool:
            return pool.map(heldout_row, HELDOUT_INDICES, chunksize=4)
    return [heldout_row(i) for i in HELDOUT_INDICES]


def heldout_marks(rows: List[Dict[str, object]]) -> Dict[str, object]:
    from . import probe_budget as pb
    stored = {int(r["index"]): r for r in (pb.measurements() or {})
              .get("heldout", ())}
    reached = [r for r in rows if r["reached"]]
    frozen_cert = [r for r in reached if r["frozen"]["certified"]]
    disagree = [r["index"] for r in frozen_cert
                if (r["rule"]["type"], r["rule"]["vertices"])
                != (r["frozen"]["type"], r["frozen"]["vertices"])]
    phase124 = [r["index"] for r in reached
                if r["index"] in stored and stored[r["index"]].get(
                    "rule_type") != r["rule"]["type"]]
    starts = sorted(r["rule"]["starts"] for r in reached)
    return {
        "walks": len(rows), "reached": len(reached),
        "rule_certified": sum(r["rule"]["certified"] for r in reached),
        "frozen_certified": len(frozen_cert),
        "agreement_disagreements": disagree,
        "budget_reached": sum(r["rule"]["starts"] >= hr.BUDGET
                              for r in reached),
        "phase124_disagreements": phase124,
        "phase124_compared": sum(1 for r in reached if r["index"] in stored),
        "moved": [{"index": r["index"], "type": r["rule"]["type"],
                   "rule_starts": r["rule"]["starts"],
                   "frozen_vertex_count": r["frozen"]["vertex_count"]}
                  for r in reached if not r["frozen"]["certified"]],
        "starts_median": starts[len(starts) // 2] if starts else 0,
        "starts_max": starts[-1] if starts else 0,
    }


def census_comparison() -> Dict[str, object]:
    """R1: ``report deep holes`` under the rule against the frozen census."""
    rule = hr.census_report(walks=3)["census"]
    frozen = dh.deep_holes_report(walks=3)["census"]

    def view(census):
        out = []
        for case in census["cases"]:
            run = case.get("run") or {}
            cl = case.get("classification") or run.get("classification") or {}
            out.append({"name": case["name"],
                        "type": run.get("niemeier_type",
                                        cl.get("niemeier_type")),
                        "certified": bool(run.get("certified",
                                                  cl.get("certified"))),
                        "starts": int((cl.get("probe") or {})
                                      .get("starts_run") or 0)})
        return out

    return {"rule": view(rule), "frozen": view(frozen),
            "types_rule": list(rule["types_exhibited"]),
            "types_frozen": list(frozen["types_exhibited"]),
            "same_types": list(rule["types_exhibited"])
            == list(frozen["types_exhibited"])}


def battery(verify: bool = True) -> Dict[str, object]:
    """The battery through the session, column 3 and two mutants each."""
    from ..runtime.parser import parse_query
    from ..runtime.session import GeometricSession
    from ..runtime import tct_engine as tct
    session = GeometricSession(domains=())
    out = []
    for qid, text, declared in BATTERY:
        query = parse_query(text)
        sol = session.solve(query)
        reason = ""
        if not sol.ok and "(" in (sol.error or ""):
            reason = sol.error.split("(", 1)[1].split(")", 1)[0]
        row: Dict[str, object] = {"id": qid, "question": text,
                                  "kind": query.kind, "ok": bool(sol.ok),
                                  "answer": sol.answer, "reason": reason,
                                  "type": (sol.payload or {}).get("type")
                                  if sol.ok else None}
        if declared[0] == "refused":
            row["as_declared"] = (not sol.ok) and reason == declared[1]
        elif declared[0] == "answered":
            row["as_declared"] = bool(sol.ok) and row["type"] == declared[1]
        else:
            row["as_declared"] = None
        if sol.ok and verify:
            trace = tct.verify_trace(tct.build_trace(sol))
            row["script"] = bool(trace.verdict.matches_column2)
            wrong_type = "E_8^3" if row["type"] != "E_8^3" else "D_24"
            mutants = [dict(sol.expected, type=wrong_type),
                       dict(sol.expected, vertex_count=str(
                           int(sol.expected["vertex_count"]) + 1))]
            rejected = 0
            for expected in mutants:
                mutated = dataclasses.replace(sol, expected=expected)
                verdict = tct.verify_trace(tct.build_trace(mutated)).verdict
                rejected += int(not verdict.matches_column2)
            row["mutants"] = len(mutants)
            row["mutants_rejected"] = rejected
        out.append(row)
    declared = [r for r in out if r["as_declared"] is not None]
    answered = [r for r in out if r["ok"]]
    return {
        "rows": out, "questions": len(out),
        "declared": len(declared),
        "as_declared": sum(1 for r in declared if r["as_declared"]),
        "reads_sound": sum(1 for r in out if r["as_declared"] is None
                           and (not r["ok"] or r.get("script", True))),
        "reads": sum(1 for r in out if r["as_declared"] is None),
        "answered": len(answered),
        "scripts": sum(1 for r in answered if r.get("script")),
        "mutants": sum(r.get("mutants", 0) for r in answered),
        "mutants_rejected": sum(r.get("mutants_rejected", 0)
                                for r in answered),
    }


def wiring() -> Dict[str, object]:
    from ..evaluation.cases import CASES
    from ..runtime.parser import parse_query
    from ..runtime.toolbox import wiring_census
    census = wiring_census()
    earlier = [c for c in CASES if c.kind != "hole"]
    diverted = [c.id for c in earlier
                if parse_query(c.question).kind == "hole"]
    return {"census": census,
            "hole_reading_reached": "hole_reading" not in census["declared"]
            and "hole_reading" not in census["undeclared"],
            "earlier_cases": len(earlier), "diverted": diverted}


def compute(jobs: Optional[int] = None,
                          verify: bool = True) -> Dict[str, object]:
    """Every measured mark of the study (F1 read from its own store)."""
    rows = heldout_rows(jobs)
    held = heldout_marks(rows)
    census = census_comparison()
    questions = battery(verify=verify)
    wire = wiring()
    frozen = bgf.current() or bgf.measurements() or {}
    c = wire["census"]
    marks = {
        "H1": held["reached"] > 0 and held["rule_certified"]
        == held["reached"],
        "H2": not held["agreement_disagreements"],
        "H3": held["budget_reached"] == 0,
        "H4": not held["phase124_disagreements"]
        and held["phase124_compared"] == held["reached"],
        "R1": census["same_types"] and all(
            r["certified"] for r in census["rule"][:5]),
        "Q1": (questions["as_declared"] == questions["declared"]
               and questions["reads_sound"] == questions["reads"]
               and (not verify or (questions["scripts"]
                                   == questions["answered"]
                                   and questions["mutants_rejected"]
                                   == questions["mutants"]))),
        "W1": (not c["undeclared"] and not c["stale_declarations"]
               and wire["hole_reading_reached"] and not wire["diverted"]),
        "F1": bool(frozen) and frozen.get("present") == frozen.get("cases")
        and frozen.get("same_status") == frozen.get("cases")
        and not frozen.get("undeclared"),
    }
    return {"heldout": held, "census": census, "questions": questions,
            "wiring": wire,
            "frozen": {k: frozen.get(k) for k in
                       ("cases", "present", "same_status", "same_text",
                        "moved", "undeclared", "audit")},
            "marks": marks, "met": sum(1 for v in marks.values() if v),
            "taken": len(marks), "rows": rows}


# ═════════════════════════════════════════════════════════════════════════
# THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

def module_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    paths = [root / n for n in sorted(set(_SOURCES))]
    if bgf.DATA_PATH.exists():
        paths.append(bgf.DATA_PATH)
    return integrity.tree_digest(paths, root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, dict):
        return {str(k): _freeze(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(v) for v in value]
    return value


def measure(jobs: Optional[int] = None) -> Dict[str, object]:
    report = compute(jobs=jobs)
    report["source_digest"] = module_digest()
    return report


def write_measurements(path: Optional[Path] = None,
                       jobs: Optional[int] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.write_text(json.dumps(_freeze(measure(jobs)), indent=1,
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


def budget_reading_report() -> Dict[str, object]:
    """The marks of the study, from the stored measurement while it is
    current (``tools budget-reading --write`` re-takes it)."""
    st = state()
    if not st["fresh"]:
        return {"available": False,
                 "reason": f"the stored measurement is {st['verdict']}; "
                           f"re-take it with `PYTHONPATH=. python3 -m "
                           f"glm_universal.tools budget-reading --write`"}
    return dict(measurements(), available=True)
