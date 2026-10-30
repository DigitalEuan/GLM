"""``glm_universal.reasoning.citation_reference`` -- the elaborator's citations.

Phase 101 (``studies/CITATION_SCOPE_STUDY.md``)
-----------------------------------------------
The citation graph of the Lean development is read from the *text* by
:mod:`glm_universal.reasoning.lean_address`, because a goal that arrives as
text has nothing else, and the address of a declaration must be computable
from what a goal can carry.  Phase 100 found that reader leaking: a bound
variable ``a`` was read as a citation of ``GLM.Heisenberg.a``.  A repair to a
reader is only as good as what it is checked against, so this module takes
the one answer that is not a reading at all -- the **elaborator's**:

    for every constant the Lean development declares, the constants of the
    same development that occur in its elaborated type or value.

That is produced by ``glm_lean/tools/CitationReference.lean``, run with
``lake env lean`` over a header importing every module of the development,
and stored in ``_data/lean_citation_reference.json`` beside the digest of the
Lean tree it was taken from (the same guard the address book carries).  Taking
it needs the compiled library, so it is a *recorded observation*: a stale
reference is reported as stale and never silently used.

Mapping constants onto declarations
-----------------------------------
The elaborator knows more constants than the line reader knows declarations:
equation lemmas ``f.eq_1``, auxiliary proofs ``f._proof_1``, match
compilations ``f.match_1``, a structure's constructor and projections.  Each
is mapped to the longest prefix of its name that *is* a parsed declaration,
so ``GLM.Sakuma.third._proof_1`` counts as ``GLM.Sakuma.third``; a constant
with no such prefix (a macro, an unnamed instance) is left out on both sides.

What the audit measures
-----------------------
For a textual graph ``G`` and the reference ``R``, over the declarations both
know:

``precision``
    the share of ``G``'s edges that ``R`` confirms.  An edge the elaborated
    term does not contain is a name the reader resolved that the compiler did
    not -- the leak, measured.
``recall_visible``
    the share of ``R``'s *visible* edges that ``G`` finds, where an edge
    ``d -> t`` is visible when ``t``'s short name occurs as an identifier of
    ``d``'s source outside comments.  Instance resolution, ``simp`` sets and
    elaborated types put constants in a term that no text names; no reader of
    the text can find those, so they are not counted against it.

Every count is an integer and every rate an exact
:class:`~fractions.Fraction` (directive D7).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Dict, FrozenSet, List, Mapping, Optional, Tuple

from ..derived import memo
from . import lean_address as la

__all__ = [
    "DATA_PATH", "LEAN_TOOL", "run_reference", "write_reference", "reference",
    "state", "reference_graph", "visible_edges", "audit", "audit_report",
    "one_letter_targets",
]

_HERE = Path(__file__).resolve()
DATA_PATH = _HERE.parent / "_data" / "lean_citation_reference.json"
LEAN_TOOL = _HERE.parent.parent.parent / "lean" / "tools" / "CitationReference.lean"
#: The Lake project root: the directory holding ``lakefile.toml``.
PROJECT_ROOT = _HERE.parent.parent.parent.parent

SCHEMA = 1


# ===========================================================================
#  Taking the reference
# ===========================================================================

def _module_names() -> List[str]:
    root = la.lean_root()
    if root is None:
        return []
    base = root.parent.parent          # .../glm_lean
    return [".".join(path.relative_to(base).with_suffix("").parts)
            for path in la.lean_files()]


def run_reference(timeout: int = 3600) -> Dict[str, Tuple[str, Tuple[str, ...]]]:
    """Run the Lean tool and parse its output: name -> (module, used names).

    Needs the library compiled (``lake build``); raises if Lean fails.
    """
    header = "".join(f"import {name}\n" for name in _module_names())
    body = LEAN_TOOL.read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".lean", delete=False,
                                     encoding="utf-8") as handle:
        handle.write(header + body)
        path = handle.name
    try:
        done = subprocess.run(["lake", "env", "lean", path], cwd=PROJECT_ROOT,
                              capture_output=True, text=True, timeout=timeout)
    finally:
        os.unlink(path)
    if done.returncode != 0:
        raise RuntimeError("lean failed:\n" + done.stdout[-2000:]
                           + done.stderr[-2000:])
    out: Dict[str, Tuple[str, Tuple[str, ...]]] = {}
    for line in done.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        name, module, used = parts
        out[name] = (module, tuple(sorted(set(used.split()))))
    return out


def _owner(name: str, parsed: FrozenSet[str]) -> Optional[str]:
    """The longest prefix of ``name`` that is a parsed declaration."""
    parts = name.replace("«", "").replace("»", "").split(".")
    for k in range(len(parts), 0, -1):
        candidate = ".".join(parts[:k])
        if candidate in parsed:
            return candidate
    return None


def map_reference(raw: Mapping[str, Tuple[str, Tuple[str, ...]]]
                  ) -> Dict[str, List[str]]:
    """The raw constant graph folded onto the parsed declarations."""
    parsed = frozenset(d.name for d in la.declarations())
    graph: Dict[str, set] = {}
    for name, (_module, used) in raw.items():
        owner = _owner(name, parsed)
        if owner is None:
            continue
        targets = graph.setdefault(owner, set())
        for constant in used:
            target = _owner(constant, parsed)
            if target is not None and target != owner:
                targets.add(target)
    return {name: sorted(targets) for name, targets in sorted(graph.items())}


def write_reference(path: Optional[Path] = None) -> Path:
    """Take the reference now and store it beside the Lean tree digest."""
    raw = run_reference()
    graph = map_reference(raw)
    record = {
        "schema": SCHEMA,
        "tree_digest": la.tree_digest(),
        "constants": len(raw),
        "graph": graph,
    }
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=0, sort_keys=True) + "\n",
                      encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def reference() -> Optional[Dict[str, object]]:
    """The stored reference, or ``None`` if it was never taken."""
    global _cache
    if _cache is None and DATA_PATH.exists():
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _cache


def state() -> Dict[str, object]:
    """Fresh, stale or absent: is the stored reference of the current tree?"""
    stored = reference()
    live = la.tree_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    fresh = stored.get("tree_digest") == live and stored.get("schema") == SCHEMA
    return {"present": True, "fresh": fresh,
            "verdict": "fresh" if fresh else "stale",
            "live_digest": live, "stored_digest": stored.get("tree_digest")}


def reference_graph() -> Dict[str, FrozenSet[str]]:
    """The elaborator's graph over the parsed declarations (empty if absent)."""
    stored = reference()
    if stored is None:
        return {}
    return {name: frozenset(targets)
            for name, targets in stored["graph"].items()}


# ===========================================================================
#  The audit
# ===========================================================================

@memo
def _visible_tokens() -> Dict[str, FrozenSet[str]]:
    """Every identifier component each declaration's code names."""
    out: Dict[str, FrozenSet[str]] = {}
    for d in la.declarations():
        text = la.strip_comments_and_strings(d.statement + "\n" + d.body)
        words = set()
        for token in la._TOKEN.findall(text):
            words.update(part for part in token.split(".") if part)
        out[d.name] = frozenset(words)
    return out


def visible_edges(ref: Mapping[str, FrozenSet[str]]) -> Dict[str, FrozenSet[str]]:
    """The reference edges whose target's short name the source spells."""
    tokens = _visible_tokens()
    short = {d.name: d.short for d in la.declarations()}
    return {name: frozenset(t for t in targets
                            if short.get(t) in tokens.get(name, ()))
            for name, targets in ref.items()}


def one_letter_targets() -> FrozenSet[str]:
    """The declarations whose short name is a single letter."""
    return frozenset(d.name for d in la.declarations() if len(d.short) == 1)


def audit(graph: Mapping[str, FrozenSet[str]],
          ref: Optional[Mapping[str, FrozenSet[str]]] = None
          ) -> Dict[str, object]:
    """Precision and visible recall of a textual graph against the reference."""
    ref = reference_graph() if ref is None else ref
    shared = sorted(set(graph) & set(ref))
    visible = visible_edges({n: ref[n] for n in shared})
    single = one_letter_targets()
    edges = confirmed = found = seen = 0
    single_edges = single_false = 0
    for name in shared:
        mine = graph[name]
        truth = ref[name]
        edges += len(mine)
        confirmed += len(mine & truth)
        seen += len(visible[name])
        found += len(mine & visible[name])
        for target in mine:
            if target in single:
                single_edges += 1
                if target not in truth:
                    single_false += 1
    return {
        "declarations": len(shared),
        "edges": edges,
        "confirmed": confirmed,
        "unconfirmed": edges - confirmed,
        "precision": Fraction(confirmed, edges) if edges else Fraction(0),
        "reference_edges": sum(len(ref[n]) for n in shared),
        "visible_edges": seen,
        "found_visible": found,
        "recall_visible": Fraction(found, seen) if seen else Fraction(0),
        "one_letter_edges": single_edges,
        "one_letter_unconfirmed": single_false,
    }


def audit_report() -> Dict[str, object]:
    """Both readers against the elaborator, with the state of the reference."""
    st = state()
    if not st["present"]:
        return {"state": st}
    ref = reference_graph()
    return {
        "state": st,
        "constants": reference().get("constants"),
        "legacy": audit(la.legacy_citation_graph(), ref),
        "scoped": audit(la.citation_graph(), ref),
    }
