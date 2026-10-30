"""``glm_universal.runtime.ast_index_report`` -- the AST index against the
marks declared in ``studies/AST_INDEX_STUDY.md`` §2 (Phase 105).

The measurement (:func:`glm_universal.reasoning.ast_index.measure`) is read
from the frozen snapshot alone; the operation's cases are
``evaluation/ast_index_cases.py``.  :func:`write_measurements` stores the
whole report beside the digest of what it was computed from, and
:func:`current` returns it while that digest holds.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional

from .. import integrity
from ..evaluation import ast_index_cases as C
from ..reasoning import ast_index as ai
from ..reasoning import sign_test as _sign_test
from . import ast_index_frames as aif
from . import question_frames as qf

__all__ = ["declared_pairs", "operation", "marks", "ast_index_report",
           "write_measurements", "current", "state", "summary_text",
           "source_digest"]

_SOURCES = (
    Path(ai.__file__),
    Path(_sign_test.__file__),
    Path(aif.__file__),
    Path(__file__),
    Path(C.__file__),
)


def source_digest() -> str:
    """The digest the stored report is current against: the snapshot and
    the code that measures it."""
    parts = [ai.frozen()["digest"].encode("utf-8")]
    for p in _SOURCES:
        parts.append(p.read_bytes())
    return integrity.sha256_hex(b"\0".join(parts))


def declared_pairs() -> Dict[str, object]:
    """Every declared pair, by the matcher and by the reference."""
    rows = []
    for a, b, declared in C.MATCH_PAIRS:
        rows.append({"left": a, "right": b, "declared": declared,
                     "matcher": ai.structurally_equal(a, b),
                     "reference": ai.reference_equal(a, b)})
    as_declared = sum(1 for r in rows if r["matcher"] == r["declared"])
    agree = sum(1 for r in rows if r["matcher"] == r["reference"])
    return {"pairs": rows, "of": len(rows), "as_declared": as_declared,
            "matcher_reference_agree": agree,
            "misdeclared": [r for r in rows if r["matcher"] != r["declared"]]}


def operation(run_scripts: bool = True) -> Dict[str, object]:
    """The declared questions and refusals through the frame layer."""
    answered = []
    for qid, question, corpus in C.QUESTIONS:
        got = qf.frame_of(question)
        reading = qf.read(question, gate=run_scripts)
        row = {"id": qid, "question": question,
               "framed": got is not None and got[0].name == "ast_index",
               "corpus_read": got[1]["corpus"] if got else None,
               "corpus_declared": corpus,
               "answered": bool(reading and reading.answered),
               "value": reading.value if reading else None,
               "gate": reading.gate[0] if reading and reading.gate else None}
        if run_scripts:
            bad = aif.mutated(question)
            row["mutant_fails"] = not qf.run_gate(bad.script)[0]
        answered.append(row)
    refused = []
    for question, code in C.REFUSALS:
        reading = qf.read(question, gate=run_scripts)
        refused.append({"question": question, "declared": code,
                        "code": reading.code if reading else None,
                        "refused": bool(reading) and not reading.answered})
    return {"questions": answered, "refusals": refused}


def _met(ok: bool) -> str:
    return "met" if ok else "not met"


def marks(measure: Dict[str, object], pairs: Dict[str, object],
          op: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    q = measure["queries"]
    inv = measure["invariance"]
    hits = measure["hits"]
    disc = measure["discordance"]["ast_v2_vs_text"]
    audit = measure["audit"]
    out: Dict[str, Dict[str, object]] = {}
    out["A1"] = {"outcome": "met" if ai.frozen_state()["intact"] else
                 "not met",
                 "figure": f"snapshot {measure['snapshot_digest'][:12]}, "
                           f"{measure['sites']} sites"}
    a2 = (pairs["as_declared"] == pairs["of"]
          and audit["disagreements"] == 0 and audit["undecided"] == 0)
    out["A2"] = {"outcome": _met(a2),
                 "figure": f"{pairs['as_declared']} of {pairs['of']} pairs as "
                           f"declared; matcher and reference agree on "
                           f"{pairs['matcher_reference_agree']} of "
                           f"{pairs['of']} pairs and on "
                           f"{audit['asked'] - audit['disagreements']} of "
                           f"{audit['asked']} measurement calls"}
    a3 = all(inv[k]["bucket"] == q and inv[k]["match"] == q for k in inv)
    out["A3"] = {"outcome": _met(a3),
                 "figure": "; ".join(f"{k} {inv[k]['bucket']}/{q}"
                                     for k in inv)}
    v1 = inv["both"]["v1"]
    out["A4"] = {"outcome": _met(Fraction(v1, q) >= Fraction(95, 100)),
                 "figure": f"{v1} of {q} under `both`"}
    a5 = (hits["ast_v2"]["1"] == q
          and Fraction(hits["text"]["1"], q) <= Fraction(75, 100)
          and Fraction(disc["sign_test"]) <= Fraction(5, 100)
          and disc["for"] > disc["against"])
    out["A5"] = {"outcome": _met(a5),
                 "figure": f"ast_v2 {hits['ast_v2']['1']}/{q}, text "
                           f"{hits['text']['1']}/{q}, discordance "
                           f"{disc['for']} : {disc['against']}"}
    s = measure["soundness"]
    out["A6"] = {"outcome": _met(s["failures"] == 0 and s["classes"] > 0),
                 "figure": f"{s['classes']} classes, {s['pairs']} pairs, "
                           f"{s['evaluations']} evaluations, "
                           f"{s['failures']} failures"}
    qs = op["questions"]
    rs = op["refusals"]
    a7 = (all(r["framed"] and r["answered"] and r["gate"] is not False and
              r["corpus_read"] == r["corpus_declared"] and
              r.get("mutant_fails", True) for r in qs)
          and all(r["refused"] and r["code"] == r["declared"] for r in rs))
    out["A7"] = {"outcome": _met(a7),
                 "figure": f"{sum(r['answered'] for r in qs)} of {len(qs)} "
                           f"answered, {sum(bool(r['gate']) for r in qs)} "
                           f"scripts verify, "
                           f"{sum(bool(r.get('mutant_fails')) for r in qs)} "
                           f"mutants fail; {sum(r['refused'] and r['code'] == r['declared'] for r in rs)} "
                           f"of {len(rs)} refusals by code"}
    return out


def ast_index_report(run_scripts: bool = True) -> Dict[str, object]:
    measure = ai.measure(stride=C.STRIDE)
    pairs = declared_pairs()
    op = operation(run_scripts=run_scripts)
    return {"phase": 105, "source_digest": source_digest(),
            "measure": measure, "pairs": pairs, "operation": op,
            "marks": marks(measure, pairs, op)}


def write_measurements(path: Optional[Path] = None) -> Path:
    report = ast_index_report(run_scripts=True)
    target = Path(path) if path is not None else ai.DATA_PATH
    target.write_text(json.dumps(report, indent=1, sort_keys=True,
                                 default=str, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    return target


def current() -> Optional[Dict[str, object]]:
    """The stored report while the digest it was taken against holds."""
    if not ai.DATA_PATH.exists():
        return None
    data = json.loads(ai.DATA_PATH.read_text(encoding="utf-8"))
    return data if data.get("source_digest") == source_digest() else None


def state() -> Dict[str, str]:
    if not ai.DATA_PATH.exists():
        return {"verdict": "absent"}
    return {"verdict": "fresh" if current() is not None else "stale"}


def summary_text(report: Dict[str, object]) -> str:
    m = report["measure"]
    lines = [f"{m['sites']} sites ({m['per_corpus']}), {m['buckets']} "
             f"buckets, {m['classes']} structural classes "
             f"({m['shared_classes']} shared by both corpora); "
             f"{m['queries']} query sites"]
    for name, h in m["hits"].items():
        lines.append(f"  {name:8} hit@1 {h['1']:4}  hit@5 {h['5']:4}")
    lines.append(f"  Phase 64 address: {m['v1_false_merges']} false merges "
                 f"over {m['v1_merged_sites']} sites")
    for name, mark in report["marks"].items():
        lines.append(f"  {name}: {mark['outcome']} -- {mark['figure']}")
    return "\n".join(lines)
