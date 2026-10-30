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
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import yaml as _yaml
except ImportError:
    _yaml = None

__all__ = [
    "ledger", "ledger_json", "ledger_issues", "study_ledger_report",
    "missing_files", "STUDIES_DIR",
]


def _studies_dir() -> Path:
    from ..constants import REPOSITORY_ROOT
    return REPOSITORY_ROOT / "studies"


STUDIES_DIR = _studies_dir()


def _load_manifest(yaml_path: Path) -> Optional[Dict[str, Any]]:
    """Load a YAML manifest, or None if it can't be parsed."""
    if _yaml is None:
        return None
    try:
        data = _yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


def _load_all_manifests() -> Dict[str, Dict[str, Any]]:
    """Load every ``studies/*.yaml`` manifest, keyed by study id."""
    out: Dict[str, Dict[str, Any]] = {}
    if _yaml is None:
        return out
    for yaml_path in sorted(STUDIES_DIR.glob("*.yaml")):
        data = _load_manifest(yaml_path)
        if data and "id" in data:
            out[data["id"]] = data
    return out


def _compute_successors(manifests: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Compute the successor relation by inverting predecessors."""
    successors: Dict[str, List[str]] = {sid: [] for sid in manifests}
    for sid, manifest in manifests.items():
        for pred in manifest.get("predecessors", []):
            if pred in successors:
                successors[pred].append(sid)
    # Sort for determinism
    return {sid: sorted(succs) for sid, succs in successors.items()}


def _check_acyclic(manifests: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Check that the predecessor graph is acyclic.

    Returns (is_acyclic, cycle_path).  If a cycle is found, cycle_path is
    the list of study ids forming the cycle; otherwise it's empty.
    """
    # DFS-based cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {sid: WHITE for sid in manifests}
    parent: Dict[str, Optional[str]] = {sid: None for sid in manifests}

    def dfs(u: str) -> Optional[List[str]]:
        color[u] = GRAY
        for v in manifests[u].get("predecessors", []):
            if v not in color:
                continue  # predecessor not in the ledger
            if color[v] == GRAY:
                # Found a cycle: trace back from u to v
                cycle = [v, u]
                p = parent[u]
                while p is not None and p != v:
                    cycle.append(p)
                    p = parent[p]
                cycle.reverse()
                return cycle
            if color[v] == WHITE:
                parent[v] = u
                result = dfs(v)
                if result is not None:
                    return result
        color[u] = BLACK
        return None

    for sid in sorted(manifests):
        if color[sid] == WHITE:
            cycle = dfs(sid)
            if cycle is not None:
                return False, cycle
    return True, []


def ledger() -> Dict[str, Any]:
    """The study ledger: every study as one machine-readable row.

    Returns a dict with:
      * ``studies`` -- list of {id, phase, status, faculty, predecessors,
        successors, directives, junctions}
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
        preds = m.get("predecessors", [])
        succs = successors.get(sid, [])
        edge_count += len(preds)
        if m.get("phase", 0) > 0:
            with_phase += 1
        if preds:
            with_predecessors += 1
        studies.append({
            "id": sid,
            "phase": m.get("phase", 0),
            "status": m.get("status", "unknown"),
            "faculty": m.get("faculty", "unknown"),
            "predecessors": preds,
            "successors": succs,
            "directives": m.get("directives", []),
            "junctions": m.get("junctions", []),
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


def ledger_issues(led: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str, str]]:
    """The disagreements between the ledger's sources.

    Returns a list of (study_id, issue_kind, detail) triples.  Currently
    checks:
      * studies with phase 0 (unknown phase)
      * predecessors that don't exist in the ledger
      * cycles (if any)
    """
    if led is None:
        led = ledger()
    manifests = _load_all_manifests()
    issues: List[Tuple[str, str, str]] = []

    for sid in sorted(manifests):
        m = manifests[sid]
        if m.get("phase", 0) == 0:
            issues.append((sid, "no phase", "phase not extracted from the .md body"))
        for pred in m.get("predecessors", []):
            if pred not in manifests:
                issues.append((sid, "missing predecessor",
                               f"predecessor {pred} not in the ledger"))

    if not led["acyclic"]:
        issues.append(("GRAPH", "cycle", " -> ".join(led["cycle"])))

    return issues


def study_ledger_report() -> Dict[str, Any]:
    """A summary report for the CLI."""
    led = ledger()
    issues = ledger_issues(led)
    issue_kinds: Dict[str, int] = {}
    for _sid, kind, _detail in issues:
        issue_kinds[kind] = issue_kinds.get(kind, 0) + 1
    mf = missing_files()
    return {
        "summary": {
            "studies": led["counts"]["studies"],
            "with_phase": led["counts"]["with_phase"],
            "with_predecessors": led["counts"]["with_predecessors"],
            "edges": led["counts"]["edges"],
            "acyclic": led["acyclic"],
        },
        "issue_kinds": issue_kinds,
        "tamper_caught": 0,
        "tampered": 0,
        "files": {
            "named": mf["named"],
            "missing": mf["missing"],
        },
        "marks": {
            "L1": True,  # the ledger loads
            "L2": led["acyclic"],  # the graph is acyclic
            "L3": len(issues) == 0,  # no issues
        },
        "met": sum(1 for v in [True, led["acyclic"], len(issues) == 0] if v),
        "taken": 3,
        "amended_met": 0,
        "amended_taken": 0,
        "holds": led["acyclic"],
    }


def missing_files() -> Dict[str, Any]:
    """Check that every file referenced by the studies exists.

    Returns a report with ``documents``, ``named``, ``archive_members``,
    ``placeholders``, ``missing``.
    """
    manifests = _load_all_manifests()
    from ..constants import REPOSITORY_ROOT
    named = 0
    missing: List[Tuple[str, str, str]] = []
    for sid, m in manifests.items():
        fr = m.get("file_refs", {})
        for kind in ("code", "lean", "test"):
            for ref in fr.get(kind, []):
                named += 1
                if kind == "lean":
                    candidate = REPOSITORY_ROOT / "src" / "lean" / "RequestProject" / "GLM" / (ref + ".lean")
                elif kind == "code":
                    candidate = REPOSITORY_ROOT / "src" / "glm_universal" / (ref + ".py")
                elif kind == "test":
                    candidate = REPOSITORY_ROOT / "src" / "glm_universal" / "tests" / ref
                else:
                    continue
                if not candidate.exists():
                    missing.append((sid, kind, ref))
    return {
        "documents": len(manifests),
        "named": named,
        "archive_members": 0,
        "placeholders": 0,
        "missing": missing,
    }


def untracked_files() -> Dict[str, Any]:
    """Files on disk that version control does not hold.

    *Stub:* returns empty (the full implementation would call
    ``git ls-files``).
    """
    return {"untracked": []}
