"""``glm_universal.reasoning.nearest_address_study`` -- the measurement of
Phase 148, the guarded read in the ``nearest`` kind.

``studies/NEAREST_ADDRESS_STUDY.md`` pre-registered the marks; this module
takes them.

* **N1-N4** -- the six query sets of Phase 143 (the four of Phase 129, the
  fifth and the clean set; 3,550 points), each point ranked against the 142
  carriers by full scan and read by the guarded read: the head against the
  read (N1), the certified gap (N2), the origin (N3), and what the ranking's
  head is worth where the read refuses (N4, described, not predicted).
* **Q1** -- the question battery of the ``nearest`` address path through the
  session, with column 3 and two mutants of every answered claim.
* **W1** -- the wiring census, and no earlier ``nearest`` case diverted to the
  address path.
* **F1, A0** -- the frozen path and the ladder audit, from
  :mod:`budget_guard_frozen`.

Stored beside the digest of its sources (``tools nearest-address --write``).

Exactness
---------
Integers, strings and :class:`fractions.Fraction` only.
"""

from __future__ import annotations

import dataclasses
import json
import multiprocessing
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity
from . import address_read as AR
from . import address_read_study as ARS
from . import address_table as AT
from . import budget_guard_frozen as bgf
from . import cell_guard as CG
from . import coordinate_junction as CJ
from . import nearest_address as NA

__all__ = [
    "BATTERY", "read_sets", "battery", "wiring", "compute", "nearest_address_report",
    "measure", "write_measurements", "measurements", "state", "current",
    "DATA_PATH",
]

#: ``(id, question, declared)``: ``("answered", head, certified)``,
#: ``("refused", reason)`` or ``("read", None)``.
BATTERY: Tuple[Tuple[str, str, tuple], ...] = (
    ("R1", "nearest to water moved 8 by 1/2", ("refused", "ambiguous-name")),
    ("R2", "nearest to Fe moved 8 by 1/2", ("refused", "unknown-name")),
    ("R3", "nearest to 1, 2, 3", ("refused", "dimension")),
    ("R4", "nearest to C moved 30 by 1/2", ("refused", "malformed")),
    ("R5", "nearest 0 to C moved 8 by 1/2", ("refused", "malformed")),
    ("B1", "nearest to C moved 8 by 1/2", ("answered", "chemistry:C", True)),
    ("B2", "nearest to " + ", ".join(["0"] + ["1"] * 12 + ["0"] * 11),
     ("answered", "mathematics:golay_codeword_1", True)),
    ("B3", "nearest 3 to harmonics:perfect_fifth moved 2 by 2",
     ("answered", "harmonics:perfect_fifth", False)),
    ("B4", "nearest to albedo moved 4 by 1/4", ("read", None)),
    ("B5", "nearest to energy moved 24 by 1/4", ("read", None)),
    ("B6", "nearest 2 to golay_codeword_1 moved 4 by 3/2", ("read", None)),
    ("B7", "nearest to " + ", ".join(["0"] * 24), ("read", None)),
    ("B8", "nearest to physics:acceleration moved 8 by 1/4 word 7",
     ("read", None)),
)

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "nearest_address_study.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/nearest_address_study.py", "reasoning/nearest_address.py",
    "reasoning/address_read.py", "reasoning/address_table.py",
    "reasoning/address_read_study.py", "reasoning/coordinate_junction.py",
    "runtime/session.py", "runtime/parser.py", "runtime/tct_engine.py",
    "runtime/toolbox.py",
)

_WORK: Dict[str, object] = {}


def _one(args) -> Dict[str, object]:
    name, truth, point, delta2 = args
    rows, table, jtable = _WORK["rows"], _WORK["table"], _WORK["jtable"]
    read = CJ.read_point(point, table, jtable, rows, delta2=delta2)
    ranked = NA.ranking(point, rows)
    best = ranked[0][1]
    head = sorted(i for i, d in ranked if d == best)
    out = {"set": name, "truth": truth, "head": head,
           "answered": read.status == "answered"}
    if out["answered"]:
        members = sorted(read.members) if read.members else [read.carrier]
        out["agrees"] = head == members
        m = read.margin
        out["margin_positive"] = m > 0
        out["gap"] = m <= 0 or (best < m * m and all(
            d >= m * m for i, d in ranked if i not in members))
        out["origin_certified"] = bool(read.origin_certified)
        out["origin_ok"] = (not read.origin_certified) or truth in members
    return out


def read_sets(jobs: int = 6) -> Dict[str, object]:
    rows = AT.carriers()
    table = AR.load_table(rows=rows)
    jtable, _state = CJ.load(rows=rows)
    sets = ARS.query_sets(rows)
    moves = ARS._moves(rows)
    _WORK.update(rows=rows, table=table, jtable=jtable)
    work = [(name, truth, query, moves[name][k])
            for name, queries in sets.items()
            for k, (truth, query) in enumerate(queries)]
    if jobs > 1:
        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(jobs) as pool:
            results = pool.map(_one, work, chunksize=24)
    else:
        results = [_one(w) for w in work]
    by_set: Dict[str, Dict[str, object]] = {}
    for name in sets:
        rs = [r for r in results if r["set"] == name]
        ans = [r for r in rs if r["answered"]]
        ref = [r for r in rs if not r["answered"]]
        by_set[name] = {
            "points": len(rs), "answered": len(ans), "refused": len(ref),
            "head_disagreements": sum(1 for r in ans if not r["agrees"]),
            "gap_violations": sum(1 for r in ans if not r["gap"]),
            "margin_positive": sum(1 for r in ans if r["margin_positive"]),
            "origin_certified": sum(1 for r in ans if r["origin_certified"]),
            "origin_violations": sum(1 for r in ans if not r["origin_ok"]),
            "refused_head_is_origin": sum(1 for r in ref
                                          if r["head"] == [r["truth"]]),
            "refused_head_tied": sum(1 for r in ref if len(r["head"]) > 1),
            "refused_head_other": sum(1 for r in ref
                                      if len(r["head"]) == 1
                                      and r["head"] != [r["truth"]]),
        }
    totals = {key: sum(v[key] for v in by_set.values())
              for key in next(iter(by_set.values()))}
    return {"sets": by_set, "totals": totals}


def battery(verify: bool = True) -> Dict[str, object]:
    from ..runtime.parser import parse_query
    from ..runtime.session import GeometricSession
    from ..runtime import tct_engine as tct
    rows = AT.carriers()
    session = GeometricSession(domains=())
    out = []
    for qid, text, declared in BATTERY:
        query = parse_query(text)
        sol = session.solve(query)
        reason = ""
        if not sol.ok and "(" in (sol.error or ""):
            reason = sol.error.split("(", 1)[1].split(")", 1)[0]
        payload = dict(sol.payload or {}) if sol.ok else {}
        row: Dict[str, object] = {
            "id": qid, "question": text, "kind": query.kind,
            "address": bool(query.options.get("address_request")),
            "ok": bool(sol.ok), "answer": sol.answer, "reason": reason,
            "head": (sol.expected or {}).get("head") if sol.ok else None,
            "certified": payload.get("certified")}
        if declared[0] == "refused":
            row["as_declared"] = (not sol.ok) and reason == declared[1] \
                and row["address"]
        elif declared[0] == "answered":
            row["as_declared"] = (bool(sol.ok) and row["head"] == declared[1]
                                  and row["certified"] == declared[2])
        else:
            row["as_declared"] = None
        if sol.ok and verify:
            trace = tct.verify_trace(tct.build_trace(sol))
            row["script"] = bool(trace.verdict.matches_column2)
            wrong = next(AR.carrier_label(rows, k) for k in range(len(rows))
                         if AR.carrier_label(rows, k) != row["head"])
            mutants = [dict(sol.expected, head=wrong)]
            if "margin" in sol.expected:
                over = Fraction(sol.expected["margin"]) * 1000 + 1000
                mutants.append(dict(sol.expected,
                                    margin=f"{over.numerator}/"
                                           f"{over.denominator}"))
            else:
                mutants.append(dict(sol.expected,
                                    top_distances2="['0/1']"))
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
        "rows": out, "questions": len(out), "declared": len(declared),
        "as_declared": sum(1 for r in declared if r["as_declared"]),
        "reads": sum(1 for r in out if r["as_declared"] is None),
        "reads_sound": sum(1 for r in out if r["as_declared"] is None
                           and r["address"]
                           and (not r["ok"] or r.get("script", True))),
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
    earlier = [c for c in CASES if c.kind == "nearest"
               and not c.id.startswith("nearest-address")]
    diverted = [c.id for c in earlier
                if parse_query(c.question).options.get("address_request")]
    return {"census": census,
            "nearest_address_reached":
                "nearest_address" not in census["declared"]
                and "nearest_address" not in census["undeclared"],
            "earlier_nearest_cases": len(earlier), "diverted": diverted}


def compute(jobs: int = 6, verify: bool = True
                           ) -> Dict[str, object]:
    sets = read_sets(jobs)
    t = sets["totals"]
    questions = battery(verify=verify)
    wire = wiring()
    frozen = bgf.current() or bgf.measurements() or {}
    c = wire["census"]
    audit = frozen.get("audit") or {}
    marks = {
        "N1": t["answered"] > 0 and t["head_disagreements"] == 0,
        "N2": t["gap_violations"] == 0,
        "N3": t["origin_violations"] == 0,
        "Q1": (questions["as_declared"] == questions["declared"]
               and questions["reads_sound"] == questions["reads"]
               and (not verify or (questions["scripts"]
                                   == questions["answered"]
                                   and questions["mutants_rejected"]
                                   == questions["mutants"]))),
        "W1": (not c["undeclared"] and not c["stale_declarations"]
               and wire["nearest_address_reached"] and not wire["diverted"]),
        "A0": bool(frozen) and audit.get("total") == 0,
        "F1": bool(frozen) and frozen.get("present") == frozen.get("cases")
        and frozen.get("same_status") == frozen.get("cases")
        and not frozen.get("undeclared"),
    }
    return {"sets": sets, "questions": questions, "wiring": wire,
            "frozen": {k: frozen.get(k) for k in
                       ("cases", "present", "same_status", "same_text",
                        "moved", "undeclared", "audit")},
            "marks": marks, "met": sum(1 for v in marks.values() if v),
            "taken": len(marks)}


def module_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    paths = [root / n for n in sorted(set(_SOURCES))]
    for extra in (AT.DATA_PATH, bgf.DATA_PATH):
        if extra.exists():
            paths.append(extra)
    return integrity.tree_digest(paths, root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, dict):
        return {str(k): _freeze(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(v) for v in value]
    return value


def measure(jobs: int = 6) -> Dict[str, object]:
    report = compute(jobs=jobs)
    report["source_digest"] = module_digest()
    return report


def write_measurements(path: Optional[Path] = None, jobs: int = 6) -> Path:
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


def nearest_address_report() -> Dict[str, object]:
    """The marks of the study, from the stored measurement while it is
    current (``tools nearest-address --write`` re-takes it)."""
    st = state()
    if not st["fresh"]:
        return {"available": False,
                 "reason": f"the stored measurement is {st['verdict']}; "
                           f"re-take it with `PYTHONPATH=. python3 -m "
                           f"glm_universal.tools nearest-address --write`"}
    return dict(measurements(), available=True)
