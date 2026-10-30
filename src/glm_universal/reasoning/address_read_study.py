"""``glm_universal.reasoning.address_read_study`` -- the marks of the address
read (Phase 143).

``studies/ADDRESS_READ_STUDY.md`` pre-registered ten marks, a fifth query set
and a question battery.  This module takes the measured ones (L1 is pinned by
the build and the test):

* **A1** -- on Phase 129's four sets, the read the `locate` kind calls names,
  query by query, the carrier a freshly computed placement-guarded ladder
  names (the table is checked against a recomputation, not against itself);
* **A2** -- every answer on every set is the strictly nearest carrier by a
  full scan, and no other carrier lies within the reported margin;
* **A3** -- the fifth set, blind: no answer names a carrier other than the
  one the query was made from;
* **A4** -- the three visiting orders agree query by query;
* **O1** -- every answer whose known move is inside the margin names the
  carrier the query was made from;
* **C1** -- no clean carrier is read as another;
* **T1** -- twelve tamperings of the table each refused ``stale-table``;
* **Q1** -- the seventeen questions through the session, their column-3
  scripts, and two mutations of every answered claim;
* **W1** -- the wiring census and the evaluation's texts (the end-to-end
  evaluation itself is run by ``python3 -m glm_universal.evaluation``).

Exactness: integers and :class:`~fractions.Fraction` throughout.
"""

from __future__ import annotations

import copy
import json
import multiprocessing
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import construction_ladder as CL
from . import address_read as AR
from . import address_table as AT
from . import cell_guard as CG
from . import ladder_escalation as LE
from . import norm256_hex as NH
from . import placement_guard as PG

__all__ = [
    "FIFTH", "FIFTH_OFFSET", "BATTERY", "TAMPERINGS", "fifth_queries",
    "clean_queries", "query_sets", "read_sets", "tamperings", "battery",
    "wiring", "address_read_report", "DATA_PATH", "module_digest", "measure",
    "write_measurements", "measurements", "state", "current",
]

#: The fifth query set of section 3.1, codeword index ``i + FIFTH_OFFSET``.
FIFTH: Tuple[Tuple[str, int, Fraction], ...] = (
    ("16 coordinates by 1/4", 16, Fraction(1, 4)),
    ("6 coordinates by 1", 6, Fraction(1)),
    ("24 coordinates by 1/2", 24, Fraction(1, 2)),
    ("3 coordinates by 3/2", 3, Fraction(3, 2)),
)
FIFTH_OFFSET = 512

#: ``(id, question, declared)``; ``declared`` is ``("refused", reason)``,
#: ``("answered", carrier, origin_certified)`` (predicted) or ``("read",)``.
_GOLAY_1 = ("0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, "
            "0, 0")
BATTERY: Tuple[Tuple[str, str, tuple], ...] = (
    ("R1", "locate water", ("refused", "ambiguous-name")),
    ("R2", "locate Fe", ("refused", "unknown-name")),
    ("R3", "locate xyz:C", ("refused", "unknown-name")),
    ("R4", "locate 1, 2, 3", ("refused", "dimension")),
    ("R5", "locate C moved 30 by 1/2", ("refused", "malformed")),
    ("R6", "locate C moved 8 by x", ("refused", "malformed")),
    ("R7", "locate C please", ("refused", "malformed")),
    ("B1", "locate C", ("answered", "chemistry:C", None)),
    ("B2", "locate molecules:water", ("answered", "molecules:water", None)),
    ("B3", "locate lexicon:water", ("answered", "lexicon:water", None)),
    ("B4", "locate C moved 8 by 1/2", ("read",)),
    ("B5", "locate energy moved 24 by 1/4", ("answered", "lexicon:energy",
                                              None)),
    ("B6", "locate perfect_fifth moved 2 by 2", ("read",)),
    ("B7", "locate physics:acceleration moved 8 by 1/4 word 7",
     ("answered", "physics:acceleration", None)),
    ("B8", "locate golay_codeword_1 moved 4 by 3/2", ("read",)),
    ("B9", "locate " + ", ".join(["0"] * 24), ("read",)),
    ("B10", f"locate {_GOLAY_1} within 1/2",
     ("answered", "mathematics:golay_codeword_1", True)),
)

#: The twelve tamperings of section 4 (mark T1).
TAMPERINGS: Tuple[str, ...] = (
    "radius raised", "radius lowered", "carrier swapped", "cell moved",
    "entry deleted", "entry added", "live carrier moved",
    "source digest altered", "carriers digest altered", "ladder reordered",
    "file truncated", "file absent")

Query = Tuple[int, Tuple[Fraction, ...]]


def fifth_queries(rows) -> List[Query]:
    """The 568 queries of the fifth set, declared in section 3.1."""
    out: List[Query] = []
    for _label, support, magnitude in FIFTH:
        for i, (_r, _n, carrier) in enumerate(rows):
            out.append((i, tuple(LE.perturb(carrier, i + FIFTH_OFFSET,
                                            support, magnitude))))
    return out


def clean_queries(rows) -> List[Query]:
    """The 142 carriers themselves."""
    return [(i, tuple(Fraction(x) for x in carrier))
            for i, (_r, _n, carrier) in enumerate(rows)]


def _moves(rows) -> Dict[str, List[Fraction]]:
    """The squared length of every query's move, set by set (the sets are
    built carrier-major within each perturbation)."""
    n = len(rows)
    sets = {
        "standard": [(s, m) for _l, s, m in LE.PERTURBATIONS],
        "held_out": [(s, m) for _l, s, m in NH.HELD_OUT],
        "third": [(s, m) for _l, s, m in CG.THIRD],
        "fourth": [(s, m) for _l, s, m in PG.FOURTH],
        "fifth": [(s, m) for _l, s, m in FIFTH],
    }
    out = {name: [s * m * m for s, m in spec for _ in range(n)]
           for name, spec in sets.items()}
    out["clean"] = [Fraction(0)] * n
    return out


def query_sets(rows) -> Dict[str, List[Query]]:
    """The four sets of Phase 129, the fifth set and the clean set."""
    sets = PG.query_sets(rows)
    sets["fifth"] = fifth_queries(rows)
    sets["clean"] = clean_queries(rows)
    return sets


# ═════════════════════════════════════════════════════════════════════════
# A1-A4, O1, C1 -- THE SETS
# ═════════════════════════════════════════════════════════════════════════

_WORK: Dict[str, object] = {}


def _reference(query, indices, rads) -> Optional[int]:
    """The placement-guarded ladder of Phase 129, middle-out, recomputed
    from fresh indices and radii (the reading of ``placement_guard.read_set``
    with ``kind == "placed"``)."""
    for rung in CL.middle_out_order(PG.LADDER):
        point = NH.quantise(query, rung)
        members = indices[rung].get(point, ())
        if len(members) != 1:
            continue
        i = members[0]
        if PG.exact_lt(CG._nsq(query, _WORK["rows"][i][2]),
                       CG._nsq(query, point), rads[rung][point]):
            return i
    return None


def _read_one(args) -> Dict[str, object]:
    name, index, truth, query, delta2 = args
    rows, table = _WORK["rows"], _WORK["table"]
    reads = {order: AR.read_point(query, table, rows, seq, delta2)
             for order, seq in (("middle_out", AR.ORDER),
                                ("coarse_to_fine", AR.LADDER),
                                ("fine_to_coarse",
                                 tuple(reversed(AR.LADDER))))}
    main = reads["middle_out"]
    out = {"set": name, "index": index, "truth": truth,
           "answer": main.carrier, "rung": main.rung,
           "orders_agree": len({r.carrier for r in reads.values()}) == 1,
           "origin_certified": bool(main.origin_certified)}
    if name != "clean" and name != "fifth":
        out["reference"] = _reference(query, _WORK["indices"], _WORK["rads"])
    if main.carrier is not None:
        dist = [CG._nsq(query, c) for (_r, _n, c) in rows]
        best = min(dist)
        nearest = [k for k, v in enumerate(dist) if v == best]
        m = main.margin
        out["strict_nearest"] = nearest == [main.carrier]
        out["margin_holds"] = m <= 0 or (
            dist[main.carrier] < m * m
            and all(v >= m * m for k, v in enumerate(dist)
                    if k != main.carrier))
        out["margin_positive"] = m > 0
    return out


def read_sets(rows=None, table=None, jobs: int = 6) -> Dict[str, object]:
    """Every set read by the stored table, scanned, and (for the four sets
    of Phase 129) compared with a recomputed placement-guarded ladder."""
    rows = rows if rows is not None else AT.carriers()
    table = table if table is not None else AR.load_table(rows=rows)
    indices = {rung: CG._index(rung, rows) for rung in PG.LADDER}
    rads = {rung: PG.radii(rung, rows, indices[rung]) for rung in PG.LADDER}
    sets = query_sets(rows)
    moves = _moves(rows)
    _WORK.update(rows=rows, table=table, indices=indices, rads=rads)
    work = [(name, k, truth, query, moves[name][k])
            for name, queries in sets.items()
            for k, (truth, query) in enumerate(queries)]
    if jobs > 1:
        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(jobs) as pool:
            results = pool.map(_read_one, work, chunksize=24)
    else:
        results = [_read_one(item) for item in work]
    by_set: Dict[str, Dict[str, object]] = {}
    for name in sets:
        rs = [r for r in results if r["set"] == name]
        answered = [r for r in rs if r["answer"] is not None]
        row = {
            "queries": len(rs),
            "correct": sum(1 for r in answered if r["answer"] == r["truth"]),
            "wrong": sum(1 for r in answered if r["answer"] != r["truth"]),
            "refused": len(rs) - len(answered),
            "not_strict_nearest": sum(1 for r in answered
                                      if not r["strict_nearest"]),
            "margin_violations": sum(1 for r in answered
                                     if not r["margin_holds"]),
            "margin_positive": sum(1 for r in answered
                                   if r["margin_positive"]),
            "orders_disagree": sum(1 for r in rs if not r["orders_agree"]),
            "origin_certified": sum(1 for r in answered
                                    if r["origin_certified"]),
            "origin_violations": sum(1 for r in answered
                                     if r["origin_certified"]
                                     and r["answer"] != r["truth"]),
            "rungs": {rung: sum(1 for r in answered if r["rung"] == rung)
                      for rung in AR.LADDER},
            "wrong_answers": [{"truth": AR.carrier_label(rows, r["truth"]),
                               "named": AR.carrier_label(rows, r["answer"]),
                               "rung": r["rung"], "index": r["index"]}
                              for r in answered if r["answer"] != r["truth"]],
        }
        if "reference" in rs[0]:
            row["reference_disagreements"] = sum(
                1 for r in rs if r["reference"] != r["answer"])
            plain = PG.read_set(rows, sets[name], indices, rads)
            totals = plain["placed"]["totals"]["middle_out"]
            row["read_set_placed"] = dict(totals)
            row["unguarded"] = dict(plain["plain"]["totals"]["middle_out"])
        by_set[name] = row
    return by_set


# ═════════════════════════════════════════════════════════════════════════
# T1 -- THE TABLE AND ITS DIGEST
# ═════════════════════════════════════════════════════════════════════════

def _tampered(stored: Dict[str, object], how: str, rows):
    """``(stored, rows, path)`` after one tampering; ``path`` is a file to
    read the table from, or ``None`` to use ``stored`` as given."""
    t = copy.deepcopy(stored)
    rung = AT.LADDER[0]
    single = t["rungs"][rung]["single"]
    rows = tuple(rows)
    path = None
    if how == "radius raised":
        single[0][2] = str(Fraction(single[0][2]) * 4)
    elif how == "radius lowered":
        single[0][2] = str(Fraction(single[0][2]) / 4)
    elif how == "carrier swapped":
        single[0][1] = (single[0][1] + 1) % len(rows)
    elif how == "cell moved":
        single[0][0] = [x + 1 for x in single[0][0]]
    elif how == "entry deleted":
        del single[0]
    elif how == "entry added":
        single.append([[0] * LE.DIM, 0, "1/1"])
    elif how == "live carrier moved":
        register, name, coords = rows[0]
        rows = ((register, name,
                 (Fraction(coords[0]) + 1,) + tuple(coords[1:])),) + rows[1:]
    elif how == "source digest altered":
        t["source_digest"] = "0" * 64
    elif how == "carriers digest altered":
        t["carriers_digest"] = "0" * 64
    elif how == "ladder reordered":
        t["ladder"] = list(reversed(t["ladder"]))
    elif how in ("file truncated", "file absent"):
        folder = Path(tempfile.mkdtemp(prefix="glm_address_"))
        path = folder / "address_table.json"
        if how == "file truncated":
            text = json.dumps(stored)
            path.write_text(text[: len(text) // 2], encoding="utf-8")
        t = AT.measurements(path=path)
    else:  # pragma: no cover
        raise KeyError(how)
    return t, rows, path


def tamperings(stored: Optional[Dict[str, object]] = None, rows=None
               ) -> Dict[str, object]:
    """Each tampering, and whether the read refused it ``stale-table``."""
    rows = rows if rows is not None else AT.carriers()
    stored = stored if stored is not None else AT.measurements()
    out: Dict[str, str] = {}
    for how in TAMPERINGS:
        t, live, _path = _tampered(stored, how, rows)
        try:
            if t is None:
                raise AR.AddressError("stale-table", "absent")
            AR.load_table(stored=t, rows=live)
            out[how] = "answered"
        except AR.AddressError as error:
            out[how] = error.reason
    refused = sum(1 for v in out.values() if v == "stale-table")
    return {"rows": out, "refused": refused, "of": len(TAMPERINGS),
            "intact_loads": _loads(stored, rows)}


def _loads(stored, rows) -> bool:
    try:
        AR.load_table(stored=stored, rows=rows)
        return True
    except AR.AddressError:
        return False


# ═════════════════════════════════════════════════════════════════════════
# Q1 -- THE QUESTIONS, THEIR SCRIPTS AND THEIR MUTATIONS
# ═════════════════════════════════════════════════════════════════════════

def battery(verify: bool = True) -> Dict[str, object]:
    """The seventeen questions through the session."""
    import dataclasses
    from ..runtime.parser import parse_query
    from ..runtime.session import GeometricSession
    from ..runtime import tct_engine as tct
    rows = AT.carriers()
    session = GeometricSession(domains=())
    out = []
    for qid, text, declared in BATTERY:
        query = parse_query(text)
        sol = session.solve(query)
        row: Dict[str, object] = {"id": qid, "question": text,
                                  "kind": query.kind, "ok": sol.ok,
                                  "answer": sol.answer,
                                  "error": sol.error or ""}
        if sol.ok:
            payload = dict(sol.payload)
            row["carrier"] = payload["carrier"]
            row["origin_certified"] = payload["origin_certified"]
            parts = AR.parse_request(str(query.options["request"]), rows)
            dist = [CG._nsq(parts["point"], c) for (_r, _n, c) in rows]
            best = min(dist)
            near = [k for k, v in enumerate(dist) if v == best]
            row["scan"] = (AR.carrier_label(rows, near[0])
                           if len(near) == 1 else None)
            row["scan_agrees"] = row["scan"] == payload["carrier"]
        reason = ""
        if not sol.ok and "(" in (sol.error or ""):
            reason = sol.error.split("(", 1)[1].split(")", 1)[0]
        row["reason"] = reason
        if declared[0] == "refused":
            row["as_declared"] = (not sol.ok) and reason == declared[1]
        elif declared[0] == "answered":
            row["as_declared"] = (sol.ok and row["carrier"] == declared[1]
                                  and (declared[2] is None
                                       or bool(row["origin_certified"])
                                       == declared[2]))
        else:
            row["as_declared"] = None
        row["sound"] = (not sol.ok) or row["scan_agrees"]
        if sol.ok and verify:
            trace = tct.verify_trace(tct.build_trace(sol))
            row["script"] = bool(trace.verdict.matches_column2)
            mutants = []
            wrong = next(AR.carrier_label(rows, k) for k in range(len(rows))
                         if AR.carrier_label(rows, k) != row["carrier"])
            mutants.append(dict(sol.expected, carrier=wrong))
            others = sorted(v for k, v in enumerate(dist)
                            if AR.carrier_label(rows, k) != row["carrier"])
            over = AR.margin_bound(others[0], Fraction(0)) + Fraction(
                2, AR.MARGIN_SCALE)
            mutants.append(dict(sol.expected,
                                margin=f"{over.numerator}/{over.denominator}"))
            rejected = 0
            for expected in mutants:
                mutated = dataclasses.replace(sol, expected=expected)
                verdict = tct.verify_trace(tct.build_trace(mutated)).verdict
                rejected += int(not verdict.matches_column2)
            row["mutants"] = len(mutants)
            row["mutants_rejected"] = rejected
        out.append(row)
    fixed = [r for r in out if r["id"].startswith("R")]
    predicted = [r for r in out if r["as_declared"] is not None
                 and r["id"].startswith("B")]
    answered = [r for r in out if r["ok"]]
    return {
        "rows": out,
        "fixed_as_declared": sum(1 for r in fixed if r["as_declared"]),
        "fixed": len(fixed),
        "predicted_as_declared": sum(1 for r in predicted
                                     if r["as_declared"]),
        "predicted": len(predicted),
        "reads_sound": sum(1 for r in out if r["id"].startswith("B")
                           and r["sound"]),
        "reads": sum(1 for r in out if r["id"].startswith("B")),
        "scripts": sum(1 for r in answered if r.get("script")),
        "answered": len(answered),
        "mutants": sum(r.get("mutants", 0) for r in answered),
        "mutants_rejected": sum(r.get("mutants_rejected", 0)
                                for r in answered),
    }


# ═════════════════════════════════════════════════════════════════════════
# W1 -- THE WIRING CENSUS AND THE EVALUATION'S TEXTS
# ═════════════════════════════════════════════════════════════════════════

def wiring() -> Dict[str, object]:
    """The census, and how many evaluation questions now read as `locate`."""
    from ..evaluation.cases import CASES
    from ..runtime.parser import parse_query
    from ..runtime.toolbox import wiring_census
    census = wiring_census()
    reached = {name for name in ("placement_guard", "cell_guard",
                                 "norm256_hex")
               if name not in census["declared"]
               and name not in census["undeclared"]}
    earlier = [c for c in CASES if c.kind != "locate"]
    diverted = [c.id for c in earlier
                if parse_query(c.question).kind == "locate"]
    return {"census": census, "guards_reached": sorted(reached),
            "earlier_cases": len(earlier), "diverted": diverted}


# ═════════════════════════════════════════════════════════════════════════
# THE REPORT
# ═════════════════════════════════════════════════════════════════════════

#: The figures of PLACEMENT_GUARD_STUDY.md section 7.2 (middle-out).
PHASE_129: Dict[str, Tuple[int, int]] = {
    "standard": (445, 0), "held_out": (402, 0), "third": (393, 0),
    "fourth": (402, 0)}


def address_read_report(jobs: int = 6, verify: bool = True
                        ) -> Dict[str, object]:
    """Every measured mark of the study."""
    rows = AT.carriers()
    stored = AT.measurements()
    sets = read_sets(rows, AR.load_table(stored=stored, rows=rows), jobs)
    tamper = tamperings(stored, rows)
    questions = battery(verify=verify)
    wire = wiring()
    census = wire["census"]
    four = ("standard", "held_out", "third", "fourth")
    marks = {
        "A1": all(sets[n]["reference_disagreements"] == 0
                  and (sets[n]["correct"], sets[n]["wrong"])
                  == (sets[n]["read_set_placed"]["correct"],
                      sets[n]["read_set_placed"]["wrong"])
                  == PHASE_129[n] for n in four),
        "A2": all(r["not_strict_nearest"] == 0 and r["margin_violations"] == 0
                  for r in sets.values()),
        "A3": sets["fifth"]["wrong"] == 0,
        "A4": all(r["orders_disagree"] == 0 for r in sets.values()),
        "O1": all(r["origin_violations"] == 0 for r in sets.values()),
        "C1": sets["clean"]["wrong"] == 0,
        "T1": tamper["refused"] == tamper["of"] and tamper["intact_loads"],
        "Q1": (questions["fixed_as_declared"] == questions["fixed"] == 7
               and questions["reads_sound"] == questions["reads"] == 10
               and questions["predicted_as_declared"]
               == questions["predicted"] == 6
               and (not verify
                    or (questions["scripts"] == questions["answered"]
                        and questions["mutants_rejected"]
                        == questions["mutants"]))),
        "W1": (not census["undeclared"] and not census["stale_declarations"]
               and len(wire["guards_reached"]) == 3
               and not wire["diverted"]),
    }
    return {"sets": sets, "tamperings": tamper, "questions": questions,
            "wiring": wire, "marks": marks,
            "met": sum(1 for v in marks.values() if v),
            "taken": len(marks)}


# ═════════════════════════════════════════════════════════════════════════
# THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "address_read_study.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/address_read_study.py", "reasoning/address_read.py",
    "reasoning/address_table.py", "runtime/session.py", "runtime/parser.py",
    "runtime/tct_engine.py", "runtime/toolbox.py") + tuple(PG._SOURCES)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from, and the
    stored table it reads."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    paths = [root / name for name in names]
    if AT.DATA_PATH.exists():
        paths.append(AT.DATA_PATH)
    return integrity.tree_digest(paths, root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def measure(jobs: int = 6) -> Dict[str, object]:
    """The whole study, recomputed."""
    report = address_read_report(jobs=jobs)
    report["source_digest"] = module_digest()
    return report


def write_measurements(path: Optional[Path] = None, jobs: int = 6) -> Path:
    """Take the measurement and store it beside its digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_freeze(measure(jobs)), indent=1,
                                 sort_keys=True, ensure_ascii=False) + "\n",
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
    """The measurement if it still describes the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
