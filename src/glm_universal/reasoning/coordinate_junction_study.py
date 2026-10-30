"""``glm_universal.reasoning.coordinate_junction_study`` -- the marks of the
register-junction round (Phase 144).

``studies/COORDINATE_JUNCTION_STUDY.md`` pre-registered nine marks and a
question battery.  This module takes the measured ones (L1 is pinned by the
build, F1 by ``python3 -m glm_universal.evaluation``):

* **J1** -- the stored junction table equals one recomputed from scratch
  (fresh cells, not the stored address table), and every entry is
  junction-sound by an exact scan;
* **J2** -- on the six sets of Phase 143, every query the Phase 143 read
  answers is answered identically, and every query it refuses is refused or
  answered with a junction of two or more members;
* **J3** -- every junction answer is the scan's least-distance set, its
  margin honest, the three orders agree on it, and a certified origin is in
  it;
* **J4** -- the clean set's duplicate carriers, read as themselves;
* **J5** -- the declarations: coverage, removal, and a stale declaration;
* **T1** -- ten tamperings of the junction table;
* **Q1** -- the ten questions through the session, their column-3 scripts,
  and three mutations of every junction answer.

Exactness: integers and :class:`~fractions.Fraction` throughout.
"""

from __future__ import annotations

import copy
import json
import multiprocessing
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity
from . import address_read as AR
from . import address_read_study as ARS
from . import address_table as AT
from . import cell_guard as CG
from . import coordinate_junction as CJ

__all__ = [
    "BATTERY", "TAMPERINGS", "DUPLICATES", "OTHER_REFUSED", "table_check",
    "read_sets", "duplicates", "declarations", "tamperings", "battery",
    "junction_report", "DATA_PATH", "module_digest", "measure",
    "write_measurements", "measurements", "state", "current",
]

_ZERO = ", ".join(["0"] * 24)

#: ``(id, question, declared)`` of the study's section 3: ``("junction",
#: members)``, ``("carrier", label)``, ``("refused", reason)`` or
#: ``("read",)``.
_ABS = ("physics:absorptance", "physics:albedo")
_ACOUSTIC = ("physics:acoustic_absorption", "physics:acoustic_intensity_level",
             "physics:acoustic_power_level")
_ZEROS = ("mathematics:golay_codeword_0", "mathematics:hexacode_word_0")
BATTERY: Tuple[Tuple[str, str, tuple], ...] = (
    ("J-B1", "locate albedo", ("junction", _ABS)),
    ("J-B2", "locate physics:absorptance", ("junction", _ABS)),
    ("J-B3", "locate filled_4x6", ("junction", CJ._FILLED)),
    ("J-B4", "locate golay_codeword_0", ("junction", _ZEROS)),
    ("J-B5", "locate acoustic_power_level", ("junction", _ACOUSTIC)),
    ("J-B6", "locate " + _ZERO, ("junction", _ZEROS)),
    ("J-B7", "locate albedo moved 1 by 1/4", ("read",)),
    ("J-B8", "locate filled_2x12 moved 4 by 1/2", ("read",)),
    ("J-B9", "locate high_denominator_2x3", ("refused", "no-certified-rung")),
    ("J-B10", "locate C", ("carrier", "chemistry:C")),
)

#: The ten tamperings of section 4 (mark T1).
TAMPERINGS: Tuple[str, ...] = (
    "radius raised", "radius lowered", "member dropped", "member added",
    "representative swapped", "entry deleted", "live carrier moved",
    "declaration altered", "address table altered", "file absent")

#: The two refused clean carriers that are not duplicates (Phase 143).
OTHER_REFUSED: Tuple[str, ...] = ("mathematics:high_denominator_2x3",
                                  "mathematics:rational_root_thirds")


def DUPLICATES(rows) -> List[int]:
    """The carriers that share their coordinates with another."""
    return sorted(i for g in CJ.junctions(rows) for i in g)


# ═════════════════════════════════════════════════════════════════════════
# J1 -- THE TABLE
# ═════════════════════════════════════════════════════════════════════════

def table_check(rows=None, stored=None) -> Dict[str, object]:
    """The stored table against a recomputation from fresh cells, and every
    entry's junction soundness by scan."""
    rows = rows if rows is not None else AT.carriers()
    stored = stored if stored is not None else CJ.measurements()
    fresh_address = AT.build(rows)
    recomputed = CJ.build(rows, fresh_address)
    same = (stored is not None
            and stored.get("rungs") == recomputed["rungs"])
    coords = [CJ._coords(rows, i) for i in range(len(rows))]
    entries = 0
    unsound = 0
    not_one_junction = 0
    for rung, cells in (stored or {}).get("rungs", {}).items():
        for point, members, rho2 in cells:
            entries += 1
            rho2 = Fraction(rho2)
            rep = coords[members[0]]
            if any(coords[m] != rep for m in members):
                not_one_junction += 1
            if any(CG._nsq(coords[k], point) < rho2
                   for k in range(len(rows)) if coords[k] != rep):
                unsound += 1
    return {"matches_recomputation": same, "entries": entries,
            "unsound": unsound, "not_one_junction": not_one_junction,
            "per_rung": {r: len(c) for r, c in
                         (stored or {}).get("rungs", {}).items()}}


# ═════════════════════════════════════════════════════════════════════════
# J2, J3 -- THE SETS
# ═════════════════════════════════════════════════════════════════════════

_WORK: Dict[str, object] = {}


def _read_one(args) -> Dict[str, object]:
    name, index, truth, query, delta2 = args
    rows, table, jtable = _WORK["rows"], _WORK["table"], _WORK["jtable"]
    plain = AR.read_point(query, table, rows, AR.ORDER, delta2)
    reads = {order: CJ.read_point(query, table, jtable, rows, seq, delta2)
             for order, seq in (("middle_out", AR.ORDER),
                                ("coarse_to_fine", AR.LADDER),
                                ("fine_to_coarse",
                                 tuple(reversed(AR.LADDER))))}
    main = reads["middle_out"]
    out = {"set": name, "index": index, "truth": truth,
           "plain": plain.carrier, "plain_rung": plain.rung,
           "answer": main.carrier, "rung": main.rung,
           "members": tuple(main.members)}
    if main.carrier is not None:
        coords = [CJ._coords(rows, k) for k in range(len(rows))]
        out["orders_agree"] = all(
            r.carrier is not None and coords[r.carrier] == coords[main.carrier]
            for r in reads.values() if r.status == "answered")
        dist = [CG._nsq(query, c) for (_r, _n, c) in rows]
        best = min(dist)
        nearest = tuple(k for k, v in enumerate(dist) if v == best)
        m = main.margin
        out["scan_is_junction"] = nearest == tuple(main.members)
        out["margin_holds"] = m <= 0 or (
            dist[main.carrier] < m * m
            and all(v >= m * m for k, v in enumerate(dist)
                    if k not in main.members))
        out["origin_certified"] = bool(main.origin_certified)
        out["truth_in"] = truth in main.members
    return out


def read_sets(rows=None, jobs: int = 6) -> Dict[str, object]:
    """Every set of Phase 143 read by both reads."""
    rows = rows if rows is not None else AT.carriers()
    table = AR.load_table(rows=rows)
    jtable, st = CJ.load(rows=rows)
    if jtable is None:
        raise RuntimeError(f"junction table {st['verdict']}: {st['failed']}")
    sets = ARS.query_sets(rows)
    moves = ARS._moves(rows)
    _WORK.update(rows=rows, table=table, jtable=jtable)
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
        junction = [r for r in answered if len(r["members"]) > 1]
        by_set[name] = {
            "queries": len(rs),
            "plain_answered": sum(1 for r in rs if r["plain"] is not None),
            "answered": len(answered),
            "single": len(answered) - len(junction),
            "junction": len(junction),
            "refused": len(rs) - len(answered),
            "changed": sum(1 for r in rs if r["plain"] is not None
                           and (r["answer"], r["rung"], len(r["members"]))
                           != (r["plain"], r["plain_rung"], 1)),
            "new_not_junction": sum(1 for r in rs if r["plain"] is None
                                    and r["answer"] is not None
                                    and len(r["members"]) < 2),
            "wrong": sum(1 for r in answered if not r["truth_in"]),
            "junction_truth_in": sum(1 for r in junction if r["truth_in"]),
            "not_scan": sum(1 for r in answered if not r["scan_is_junction"]),
            "margin_violations": sum(1 for r in answered
                                     if not r["margin_holds"]),
            "orders_disagree": sum(1 for r in answered
                                   if not r["orders_agree"]),
            "origin_certified": sum(1 for r in answered
                                    if r["origin_certified"]),
            "origin_violations": sum(1 for r in answered
                                     if r["origin_certified"]
                                     and not r["truth_in"]),
            "junction_answers": sorted({
                "|".join(AR.carrier_label(rows, m) for m in r["members"])
                for r in junction}),
        }
    return by_set


# ═════════════════════════════════════════════════════════════════════════
# J4 -- THE DUPLICATES ON THE CLEAN SET
# ═════════════════════════════════════════════════════════════════════════

def duplicates(rows=None) -> Dict[str, object]:
    """Each refused clean carrier of Phase 143, read by the junction read."""
    rows = rows if rows is not None else AT.carriers()
    table = AR.load_table(rows=rows)
    jtable, _st = CJ.load(rows=rows)
    dup = DUPLICATES(rows)
    out = []
    for i in range(len(rows)):
        plain = AR.read_point(rows[i][2], table, rows)
        if plain.status == "answered":
            continue
        read = CJ.read_point(rows[i][2], table, jtable, rows)
        own = tuple(k for k in range(len(rows))
                    if CJ._coords(rows, k) == CJ._coords(rows, i))
        out.append({"carrier": AR.carrier_label(rows, i),
                    "duplicate": i in dup,
                    "status": read.status, "rung": read.rung,
                    "own_junction": (read.status == "answered"
                                     and tuple(read.members) == own),
                    "margin": (None if read.margin is None
                               else AR.margin_text(read.margin))})
    dups = [r for r in out if r["duplicate"]]
    others = [r for r in out if not r["duplicate"]]
    return {"rows": out, "duplicates": len(dups),
            "duplicates_read": sum(1 for r in dups if r["own_junction"]),
            "others": [r["carrier"] for r in others],
            "others_refused": sum(1 for r in others
                                  if r["status"] != "answered")}


# ═════════════════════════════════════════════════════════════════════════
# J5 -- THE DECLARATIONS
# ═════════════════════════════════════════════════════════════════════════

def declarations(rows=None) -> Dict[str, object]:
    """Coverage of the answerable junctions; each declaration removed (the
    table re-taken under the reduced declarations); a stale declaration."""
    rows = rows if rows is not None else AT.carriers()
    table = AR.load_table(rows=rows)
    address = AT.measurements()
    live = CJ.junctions(rows)
    jtable, _st = CJ.load(rows=rows)
    answerable = []
    for g in live:
        read = CJ.read_point(rows[g[0]][2], table, jtable, rows)
        if read.status == "answered" and len(read.members) > 1:
            answerable.append(CJ._labels(rows, g))
    covered = sum(1 for labels in answerable
                  if CJ.declaration_for(labels) is not None)
    removals = []
    for dec in CJ.DECLARATIONS:
        reduced = tuple(d for d in CJ.DECLARATIONS if d is not dec)
        stored = CJ.build(rows, address, reduced)
        stored["source_digest"] = CJ.module_digest()
        jt, st = CJ.load(stored, rows, address, reduced)
        index = next(k for k in range(len(rows))
                     if AR.carrier_label(rows, k) == dec.members[0])
        read = CJ.read_point(rows[index][2], table, jt, rows)
        text = (CJ.describe(CJ._labels(rows, read.members), reduced)
                if read.status == "answered" and len(read.members) > 1
                else "")
        removals.append({
            "removed": dec.members[0], "table_fresh": st["fresh"],
            "answered": read.status == "answered",
            "undeclared": "undeclared" in text,
            "identity": "identity" in text})
    stale_dec = CJ.DECLARATIONS + (CJ.Declaration(
        ("physics:absorptance", "chemistry:C"), "identity", "tamper",
        "tamper"),)
    stale = CJ.state(None, rows, address, stale_dec)
    return {"answerable": len(answerable), "covered": covered,
            "removals": removals,
            "stale_declaration_refused": "declarations" in stale["failed"]}


# ═════════════════════════════════════════════════════════════════════════
# T1 -- THE DIGESTS
# ═════════════════════════════════════════════════════════════════════════

def _tampered(stored, how: str, rows, address):
    t = copy.deepcopy(stored)
    rows = tuple(rows)
    address = copy.deepcopy(address)
    decs = CJ.DECLARATIONS
    rung = next(r for r in AT.LADDER if t["rungs"][r])
    entry = t["rungs"][rung][0]
    if how == "radius raised":
        entry[2] = str(Fraction(entry[2]) * 4)
    elif how == "radius lowered":
        entry[2] = str(Fraction(entry[2]) / 4)
    elif how == "member dropped":
        entry[1] = entry[1][1:]
    elif how == "member added":
        entry[1] = entry[1] + [0]
    elif how == "representative swapped":
        entry[1] = [entry[1][-1]] + entry[1][:-1]
        if entry[1] == stored["rungs"][rung][0][1]:      # pragma: no cover
            entry[1] = entry[1][::-1]
    elif how == "entry deleted":
        del t["rungs"][rung][0]
    elif how == "live carrier moved":
        register, name, coords = rows[0]
        rows = ((register, name,
                 (Fraction(coords[0]) + 1,) + tuple(coords[1:])),) + rows[1:]
    elif how == "declaration altered":
        d = decs[0]
        decs = (CJ.Declaration(d.members, "identity", d.why, d.relation),
                ) + decs[1:]
    elif how == "address table altered":
        single = address["rungs"][AT.LADDER[0]]["single"]
        single[0][2] = str(Fraction(single[0][2]) * 4)
    elif how == "file absent":
        t = CJ.measurements(path=Path("/nonexistent/junction_table.json"))
    else:  # pragma: no cover
        raise KeyError(how)
    return t, rows, address, decs


def tamperings(rows=None) -> Dict[str, object]:
    """Each tampering, whether the junction table was refused, and whether
    any junction answer came out of it."""
    rows = rows if rows is not None else AT.carriers()
    stored = CJ.measurements()
    address = AT.measurements()
    table = AR.load_table(rows=rows)
    out: Dict[str, Dict[str, object]] = {}
    for how in TAMPERINGS:
        t, live, addr, decs = _tampered(stored, how, rows, address)
        if t is None:                       # the file is gone: nothing loads
            jt, st = None, {"failed": ("absent",)}
        else:
            jt, st = CJ.load(t, live, addr, decs)
        answers = 0
        for i in DUPLICATES(rows):
            read = CJ.read_point(rows[i][2], table, jt, rows)
            answers += int(read.status == "answered"
                           and len(read.members) > 1)
        out[how] = {"refused": jt is None, "failed": list(st["failed"]),
                    "junction_answers": answers}
    refused = sum(1 for v in out.values()
                  if v["refused"] and v["junction_answers"] == 0)
    intact, _st = CJ.load(stored, rows, address)
    return {"rows": out, "refused": refused, "of": len(TAMPERINGS),
            "intact_loads": intact is not None}


# ═════════════════════════════════════════════════════════════════════════
# Q1 -- THE QUESTIONS
# ═════════════════════════════════════════════════════════════════════════

def battery(verify: bool = True) -> Dict[str, object]:
    """The ten questions through the session, their scripts and mutations."""
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
        reason = ""
        if not sol.ok and "(" in (sol.error or ""):
            reason = sol.error.split("(", 1)[1].split(")", 1)[0]
        row["reason"] = reason
        junction: Tuple[str, ...] = ()
        if sol.ok:
            payload = dict(sol.payload)
            junction = tuple(payload.get("junction") or ())
            row["carrier"] = payload["carrier"]
            row["junction"] = list(junction)
        if declared[0] == "junction":
            row["as_declared"] = sol.ok and set(junction) == set(declared[1])
        elif declared[0] == "carrier":
            row["as_declared"] = (sol.ok and not junction
                                  and row["carrier"] == declared[1])
        elif declared[0] == "refused":
            row["as_declared"] = (not sol.ok) and reason == declared[1]
        else:
            row["as_declared"] = None
        if sol.ok and verify:
            trace = tct.verify_trace(tct.build_trace(sol))
            row["script"] = bool(trace.verdict.matches_column2)
            if junction:
                parts = AR.parse_request(str(query.options["request"]), rows)
                dist = sorted((CG._nsq(parts["point"], c),
                               AR.carrier_label(rows, k))
                              for k, (_r, _n, c) in enumerate(rows))
                stranger = next(lab for _d, lab in dist
                                if lab not in junction)
                others = [d for d, lab in dist if lab not in junction]
                over = AR.margin_bound(others[0], Fraction(0)) + Fraction(
                    2, AR.MARGIN_SCALE)
                mutants = [
                    dict(sol.expected, junction="|".join(junction[1:])),
                    dict(sol.expected,
                         junction="|".join(junction + (stranger,))),
                    dict(sol.expected,
                         margin=f"{over.numerator}/{over.denominator}"),
                ]
                rejected = 0
                for expected in mutants:
                    mutated = dataclasses.replace(sol, expected=expected)
                    verdict = tct.verify_trace(
                        tct.build_trace(mutated)).verdict
                    rejected += int(not verdict.matches_column2)
                row["mutants"] = len(mutants)
                row["mutants_rejected"] = rejected
        out.append(row)
    predicted = [r for r in out if r["as_declared"] is not None]
    answered = [r for r in out if r["ok"]]
    return {
        "rows": out,
        "predicted": len(predicted),
        "as_declared": sum(1 for r in predicted if r["as_declared"]),
        "missed": [r["id"] for r in predicted if not r["as_declared"]],
        "answered": len(answered),
        "scripts": sum(1 for r in answered if r.get("script")),
        "mutants": sum(r.get("mutants", 0) for r in answered),
        "mutants_rejected": sum(r.get("mutants_rejected", 0)
                                for r in answered),
    }


# ═════════════════════════════════════════════════════════════════════════
# THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def junction_report(jobs: int = 6, verify: bool = True) -> Dict[str, object]:
    """Every measured mark of the study, and the census."""
    rows = AT.carriers()
    table = table_check(rows)
    sets = read_sets(rows, jobs)
    dup = duplicates(rows)
    decl = declarations(rows)
    tamper = tamperings(rows)
    questions = battery(verify=verify)
    census = CJ.census()
    marks = {
        "J1": (table["matches_recomputation"] and table["unsound"] == 0
               and table["not_one_junction"] == 0),
        "J2": all(r["changed"] == 0 and r["new_not_junction"] == 0
                  for r in sets.values()),
        "J3": all(r["not_scan"] == 0 and r["margin_violations"] == 0
                  and r["orders_disagree"] == 0 and r["origin_violations"] == 0
                  for r in sets.values()),
        "J4": (dup["duplicates"] == dup["duplicates_read"] == 15
               and sorted(dup["others"]) == sorted(OTHER_REFUSED)
               and dup["others_refused"] == 2),
        "J5": (decl["covered"] == decl["answerable"]
               and len(decl["removals"]) == 4
               and all(r["table_fresh"] and r["answered"] and r["undeclared"]
                       and not r["identity"] for r in decl["removals"])
               and decl["stale_declaration_refused"]),
        "T1": tamper["refused"] == tamper["of"] and tamper["intact_loads"],
        "Q1": (questions["as_declared"] == questions["predicted"] == 8
               and (not verify
                    or (questions["scripts"] == questions["answered"]
                        and questions["mutants_rejected"]
                        == questions["mutants"]))),
    }
    return {"table": table, "sets": sets, "duplicates": dup,
            "declarations": decl, "tamperings": tamper,
            "questions": questions, "census": census, "marks": marks,
            "met": sum(1 for v in marks.values() if v),
            "taken": len(marks)}


# ═════════════════════════════════════════════════════════════════════════
# THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH: Path = (Path(__file__).resolve().parent / "_data"
                   / "coordinate_junction_study.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/coordinate_junction_study.py",
    "reasoning/coordinate_junction.py", "reasoning/address_read.py",
    "reasoning/address_read_study.py", "reasoning/address_table.py",
    "runtime/session.py", "runtime/parser.py", "runtime/tct_engine.py",
    "reasoning/escalation.py") + tuple(AT._SOURCES)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from and the
    two stored tables it reads."""
    root = Path(__file__).resolve().parent.parent
    names = sorted(set(_SOURCES))
    paths = [root / name for name in names]
    for extra in (AT.DATA_PATH, CJ.DATA_PATH):
        if extra.exists():
            paths.append(extra)
    return integrity.tree_digest(paths, root)


def measure(jobs: int = 6) -> Dict[str, object]:
    """The whole study, recomputed."""
    report = junction_report(jobs=jobs)
    report["source_digest"] = module_digest()
    return report


def write_measurements(path: Optional[Path] = None, jobs: int = 6) -> Path:
    """Take the measurement and store it beside its digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(ARS._freeze(measure(jobs)), indent=1,
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
