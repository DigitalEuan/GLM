"""``glm_universal.corpus.study_ledger`` -- the study ledger, rebuilt.

The study ledger reads every ``studies/*.yaml`` manifest, builds the
predecessor/successor graph, and verifies it is acyclic (a study's
predecessors must have strictly earlier phases, so the relation is
acyclic by construction; the ledger confirms this).

The ledger is the structural face of D5 ("a study is not finished until
implemented, wired, tested, formalised, verified") and D15 ("a round
names which faculty it moved") for the study graph: it is the single
source of truth for "which study builds on which?".

*Rebuilt 29 October 2026 (Iteration 10 of the reorganisation).  The
original Phase 161 ledger lived in this module but was lost in the
upload; this version reads the YAML manifests (which now carry the
predecessor edges, populated by the converter in iteration 9) instead of
parsing the .md bodies directly.  The acyclicity check is the Python
face of the Lean theorem ``GLM.StudyLedger.no_cycle`` (to be rebuilt).*

*Last altered 31 October 2026 (repository check): the manifests are read
through :func:`glm_universal.corpus.study_manifest.load_manifests`, the one
loader the study index shares, and the studies folder comes from
``constants.STUDIES_DIR`` (D21); the predecessor edges are now derived from
each study's links by ``study_manifest --sync`` (a link to a study of strictly
earlier phase), so the ledger also checks that every edge points to an
earlier phase; ``missing_files`` reads the file references in their new form
(code paths relative to ``src/glm_universal``; Lean files through
``constants.lean_file``, so a held file counts as present; the cited files
recorded missing count as missing); the tamper control is real (each of the
first seven edges reversed in a copy of the graph must be seen as a cycle);
``untracked_files`` says plainly that it does not consult version control.*
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

from .. import constants as C
from . import study_manifest as sm

__all__ = [
    "ledger", "ledger_json", "ledger_issues", "study_ledger_report",
    "missing_files", "untracked_files", "tamper_control", "STUDIES_DIR",
]

#: The studies folder (``constants.STUDIES_DIR``; kept as a module name
#: because callers import it from here).
STUDIES_DIR: Path = C.STUDIES_DIR

#: How many edges the tamper control reverses.
TAMPER_EDGES = 7


def _load_all_manifests() -> Dict[str, Dict[str, Any]]:
    """Every study manifest, keyed by study id (the shared loader)."""
    return {sid: dict(data) for sid, data in sm.load_manifests().items()}


def _preds(manifest: Mapping[str, Any]) -> List[str]:
    preds = manifest.get("predecessors") or []
    return [p for p in preds if isinstance(p, str)]


def _compute_successors(manifests: Mapping[str, Mapping[str, Any]]
                        ) -> Dict[str, List[str]]:
    """Compute the successor relation by inverting predecessors."""
    successors: Dict[str, List[str]] = {sid: [] for sid in manifests}
    for sid, manifest in manifests.items():
        for pred in _preds(manifest):
            if pred in successors:
                successors[pred].append(sid)
    return {sid: sorted(succs) for sid, succs in successors.items()}


def _check_acyclic(manifests: Mapping[str, Mapping[str, Any]]
                   ) -> Tuple[bool, List[str]]:
    """Check that the predecessor graph is acyclic.

    Returns (is_acyclic, cycle_path).  If a cycle is found, cycle_path is
    the list of study ids forming the cycle; otherwise it's empty.
    Iterative, so a long chain cannot exhaust the recursion limit.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {sid: WHITE for sid in manifests}
    for root in sorted(manifests):
        if color[root] != WHITE:
            continue
        path: List[str] = [root]
        iters = [iter(_preds(manifests[root]))]
        color[root] = GRAY
        while iters:
            advanced = False
            for nxt in iters[-1]:
                if nxt not in color:
                    continue  # a predecessor not in the ledger
                if color[nxt] == GRAY:
                    start = path.index(nxt)
                    return False, path[start:] + [nxt]
                if color[nxt] == WHITE:
                    color[nxt] = GRAY
                    path.append(nxt)
                    iters.append(iter(_preds(manifests[nxt])))
                    advanced = True
                    break
            if not advanced:
                color[path.pop()] = BLACK
                iters.pop()
    return True, []


def ledger() -> Dict[str, Any]:
    """The study ledger: every study as one machine-readable row.

    Returns a dict with:
      * ``studies`` -- list of {id, title, phase, status, faculty,
        predecessors, successors, related, directives, junctions, marks
        (counts), lean_missing, lean_held}
      * ``edges`` -- the predecessor edge count
      * ``acyclic`` -- whether the graph is acyclic
      * ``cycle`` -- the cycle path if not acyclic
      * ``counts`` -- {studies, with_phase, with_predecessors, edges}
    """
    manifests = _load_all_manifests()
    successors = _compute_successors(manifests)
    is_acyclic, cycle = _check_acyclic(manifests)

    studies: List[Dict[str, Any]] = []
    edge_count = 0
    with_phase = 0
    with_predecessors = 0

    for sid in sorted(manifests):
        m = manifests[sid]
        preds = _preds(m)
        succs = successors.get(sid, [])
        edge_count += len(preds)
        phase = m.get("phase", 0) or 0
        if phase > 0:
            with_phase += 1
        if preds:
            with_predecessors += 1
        marks = m.get("marks") or {}
        refs = m.get("file_refs") or {}
        studies.append({
            "id": sid,
            "title": m.get("title", ""),
            "phase": phase,
            "status": m.get("status", "unknown"),
            "faculty": m.get("faculty", "unknown"),
            "predecessors": preds,
            "successors": succs,
            "related": list(m.get("related") or []),
            "directives": list(m.get("directives") or []),
            "junctions": list(m.get("junctions") or []),
            "marks": {k: len(marks.get(k) or [])
                      for k in ("declared", "met", "missed", "amended")},
            "lean_missing": list(refs.get("lean_missing") or []),
            "lean_held": list(refs.get("lean_held") or []),
        })

    return {
        "studies": studies,
        "edges": edge_count,
        "acyclic": is_acyclic,
        "cycle": cycle,
        "counts": {
            "studies": len(studies),
            "with_phase": with_phase,
            "with_predecessors": with_predecessors,
            "edges": edge_count,
        },
    }


def ledger_json() -> str:
    """The ledger as a JSON string."""
    return json.dumps(ledger(), indent=1, sort_keys=True, default=str) + "\n"


def ledger_issues(led: Optional[Dict[str, Any]] = None
                  ) -> List[Tuple[str, str, str]]:
    """The disagreements between the ledger's sources.

    Returns a list of (study_id, issue_kind, detail) triples:
      * ``no phase`` -- no phase could be read for the study;
      * ``missing predecessor`` -- an edge to a study with no manifest;
      * ``predecessor not earlier`` -- an edge whose target's phase is not
        strictly earlier (the derivation never writes one; a hand edit can);
      * ``cycle`` -- if any.
    """
    if led is None:
        led = ledger()
    manifests = _load_all_manifests()
    issues: List[Tuple[str, str, str]] = []
    for sid in sorted(manifests):
        m = manifests[sid]
        phase = m.get("phase", 0) or 0
        if phase == 0:
            issues.append((sid, "no phase",
                           "no phase read from the .md or the round records"))
        for pred in _preds(m):
            if pred not in manifests:
                issues.append((sid, "missing predecessor",
                               f"predecessor {pred} not in the ledger"))
                continue
            other = manifests[pred].get("phase", 0) or 0
            if not (phase > 0 and 0 < other < phase):
                issues.append((sid, "predecessor not earlier",
                               f"{pred} (phase {other}) is not earlier than "
                               f"phase {phase}"))
    if not led["acyclic"]:
        issues.append(("GRAPH", "cycle", " -> ".join(led["cycle"])))
    return issues


def tamper_control(edges: int = TAMPER_EDGES) -> Dict[str, int]:
    """Reverse each of the first ``edges`` predecessor edges (sorted) in a
    copy of the graph -- the predecessor made to build on its successor --
    and count how often the cycle check sees it.  Every reversal closes a
    cycle, so a sound check sees all of them."""
    manifests = _load_all_manifests()
    pairs = sorted((sid, pred) for sid, m in manifests.items()
                   for pred in _preds(m) if pred in manifests)[:edges]
    caught = 0
    for sid, pred in pairs:
        copy = {k: dict(v) for k, v in manifests.items()}
        copy[pred]["predecessors"] = _preds(copy[pred]) + [sid]
        acyclic, _cycle = _check_acyclic(copy)
        caught += int(not acyclic)
    return {"tampered": len(pairs), "caught": caught}


def study_ledger_report() -> Dict[str, Any]:
    """A summary report for the CLI (``tools study-ledger``)."""
    led = ledger()
    issues = ledger_issues(led)
    issue_kinds: Dict[str, int] = {}
    for _sid, kind, _detail in issues:
        issue_kinds[kind] = issue_kinds.get(kind, 0) + 1
    mf = missing_files()
    tamper = tamper_control()
    ordered = not any(kind in ("missing predecessor", "predecessor not earlier")
                      for _s, kind, _d in issues)
    marks = {
        "L1": led["counts"]["studies"] > 0,      # the ledger loads
        "L2": bool(led["acyclic"]),              # the graph is acyclic
        "L3": ordered,                            # every edge to an earlier phase
        "L4": tamper["caught"] == tamper["tampered"] and tamper["tampered"] > 0,
    }
    return {
        "summary": {
            "studies": led["counts"]["studies"],
            "with_phase": led["counts"]["with_phase"],
            "with_predecessors": led["counts"]["with_predecessors"],
            "edges": led["counts"]["edges"],
            "acyclic": led["acyclic"],
        },
        "issue_kinds": issue_kinds,
        "tamper_caught": tamper["caught"],
        "tampered": tamper["tampered"],
        "files": {
            "named": mf["named"],
            "missing": mf["missing"],
        },
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
        "amended_met": 0,
        "amended_taken": 0,
        "holds": bool(led["acyclic"]) and ordered,
    }


def missing_files() -> Dict[str, Any]:
    """Check that every file referenced by the studies exists.

    Returns a report with ``documents``, ``named``, ``archive_members``,
    ``placeholders``, ``missing`` (a list of ``(study, kind, ref)``).  A Lean
    file held in ``src/lean/awaiting_recovery`` exists; the files a manifest
    records as missing (``file_refs.lean_missing`` and ``file_refs.missing``)
    are missing.
    """
    manifests = _load_all_manifests()
    package = C.PACKAGE_ROOT
    named = 0
    missing: List[Tuple[str, str, str]] = []
    for sid in sorted(manifests):
        fr = manifests[sid].get("file_refs") or {}
        for kind in ("code", "lean", "test"):
            for ref in fr.get(kind) or []:
                named += 1
                if kind == "lean":
                    candidate = C.lean_file(ref)
                elif kind == "code":
                    candidate = package / ref
                else:
                    candidate = package / "tests" / ref
                if not candidate.is_file():
                    missing.append((sid, kind, ref))
        for ref in fr.get("lean_missing") or []:
            named += 1
            missing.append((sid, "lean", ref))
        for ref in fr.get("missing") or []:
            named += 1
            missing.append((sid, "test" if ref.startswith("tests/") else "code",
                            ref))
    return {
        "documents": len(manifests),
        "named": named,
        "archive_members": 0,
        "placeholders": 0,
        "missing": missing,
    }


def untracked_files() -> Dict[str, Any]:
    """Files on disk that version control does not hold.

    *Not measured:* the ledger does not run ``git`` (the repository travels
    as an upload, and the history does not always travel with it), so this
    reports nothing rather than guessing; ``measured`` says so.
    """
    return {"untracked": [], "measured": False}
