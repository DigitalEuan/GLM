"""``glm_universal.runtime.dependency_report`` -- the dependency operation
against the marks declared in ``studies/CITATION_SCOPE_STUDY.md`` §2.1
(Phase 101).

* **D1** the twelve declared questions answered as declared;
* **D2** every answer passes its column-3 gate and every mutated reading
  fails it;
* **D3** the three named refusals.

D4 (the earlier framed answers unchanged) is read by the suites that pin
them, ``tests/test_question_frames.py`` and ``tests/test_symbolic.py``.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from ..reasoning import citation_reference as cr
from ..reasoning import proof_dependency as pd
from . import dependency_frames as df
from . import question_frames as qf

__all__ = ["DECLARED", "REFUSALS", "dependency_report"]

#: The declared cases of the study's §2.1, in its order.
DECLARED: Tuple[Tuple[str, bool], ...] = (
    ("does cites_mem rest on resolve_mem", True),
    ("does cites_mem rest on resolve", True),
    ("does resolve_first rest on candidates", True),
    ("does candidates rest on prefixes", True),
    ("does scoped_reads_in_scope rest on toyCorpus", True),
    ("does legacy_reads_bound_variable rest on legacy", True),
    ("does typeCount_rename rest on typeCount", True),
    ("does infixCount_not_rename_invariant rest on typeCount", True),
    ("does resolve_mem rest on cites", False),
    ("does typeCount rest on resolve", False),
    ("does prefixes rest on candidates", False),
    ("does resolve_mem rest on GLM.Heisenberg.a", False),
)

#: The two refusals that need no change of state, with their codes.
REFUSALS: Tuple[Tuple[str, str], ...] = (
    ("does no_such_declaration_anywhere rest on resolve", "UNKNOWN_DECLARATION"),
    ("what does mul rest on", "AMBIGUOUS_NAME"),
)

#: The closure questions whose gate and mutation are also checked.
CLOSURES: Tuple[str, ...] = (
    "what does GLM.CitationScope.cites_antitone rest on",
    "what rests on GLM.CitationScope.prefixes",
    "which declarations rest on GLM.Golay24.Word",
)


def _stale_refusal() -> str:
    """The code a reference of another tree is refused with."""
    stored = cr.reference()
    saved_path, saved_cache = cr.DATA_PATH, cr._cache
    with tempfile.TemporaryDirectory() as tmp:
        fake = dict(stored or {"schema": cr.SCHEMA, "graph": {}})
        fake["tree_digest"] = "another-tree"
        path = Path(tmp) / "ref.json"
        path.write_text(json.dumps(fake), encoding="utf-8")
        cr.DATA_PATH, cr._cache = path, None
        pd._cache.clear()
        try:
            reading = df.read_dependency(df.match_raw(DECLARED[0][0]))
        finally:
            cr.DATA_PATH, cr._cache = saved_path, saved_cache
            pd._cache.clear()
    return reading.code or "ANSWERED"


def _declared_rows() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for text, declared in DECLARED:
        g = df.match_raw(text)
        reading = df.read_dependency(g)
        gate = qf.run_gate(reading.script)[0] if reading.answered else False
        bad = df.read_dependency(g, mutate=True)
        rejected = not qf.run_gate(bad.script)[0]
        got = (reading.value.startswith("yes") if reading.answered else None)
        rows.append({"question": text, "declared": declared, "got": got,
                     "value": reading.value, "gate": gate,
                     "mutation_rejected": rejected, "code": reading.code})
    return rows


def dependency_report() -> Dict[str, object]:
    saved = pd.SCOPED_QUESTIONS
    pd.SCOPED_QUESTIONS = False
    try:
        as_declared = _declared_rows()
    finally:
        pd.SCOPED_QUESTIONS = saved
    rows = _declared_rows()
    closures = []
    for text in CLOSURES:
        g = df.match_raw(text)
        reading = df.read_dependency(g)
        closures.append({
            "question": text, "answered": reading.answered,
            "value": reading.value,
            "gate": reading.answered and qf.run_gate(reading.script)[0],
            "mutation_rejected": not qf.run_gate(
                df.read_dependency(g, mutate=True).script)[0]})
    refusals = [{"question": text, "expected": code,
                 "got": df.read_dependency(df.match_raw(text)).code}
                for text, code in REFUSALS]
    refusals.append({"question": "(a reference of another tree)",
                     "expected": "REFERENCE_STALE", "got": _stale_refusal()})
    right = sum(1 for r in rows if r["got"] == r["declared"])
    first = sum(1 for r in as_declared if r["got"] == r["declared"])
    first_wrong = sum(1 for r in as_declared
                      if r["got"] is not None and r["got"] != r["declared"])
    marks = {
        "D1": first == len(DECLARED),
        "D1_after_repair": right == len(DECLARED),
        "D2": (all(r["gate"] and r["mutation_rejected"] for r in rows)
               and all(c["gate"] and c["mutation_rejected"]
                       for c in closures)),
        "D3": all(r["got"] == r["expected"] for r in refusals),
    }
    return {"declared": rows, "right": right, "wrong": len(rows) - right,
            "as_declared": {"right": first, "wrong": first_wrong,
                            "refused": sum(1 for r in as_declared
                                           if r["got"] is None),
                            "codes": sorted({r["code"] for r in as_declared
                                             if r["code"]})},
            "closures": closures, "refusals": refusals, "marks": marks,
            "reference": cr.state()["verdict"]}
