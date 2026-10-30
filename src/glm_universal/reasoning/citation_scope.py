"""``glm_universal.reasoning.citation_scope`` -- the citation repair, measured.

Phase 101 (``studies/CITATION_SCOPE_STUDY.md``)
-----------------------------------------------
Round 9 of the order of work, item 5 with the citation leak.  Two readings
of the Lean corpus were meant to be structural and were not:

* the **citation reader** resolved a token by its unique short name anywhere
  in the development, so a bound variable ``a`` read as a citation of
  ``GLM.Heisenberg.a`` (Phase 100, ``CORPUS_RESAMPLE_STUDY.md`` §4.4);
* the **feature map** counted a type word wherever it occurred, inside an
  identifier included, so renaming a statement moved a structural
  coordinate (item 5 of ``STATUS.md`` §3.4).

Both are repaired in :mod:`glm_universal.reasoning.lean_address`
(``citation_graph`` read in Lean's scope, ``type_words`` counted as whole
identifiers).  This module measures the repair against the marks the study
declared before it was taken:

``audit``
    both citation readers against the elaborator's own graph
    (:mod:`glm_universal.reasoning.citation_reference`) -- marks L1 to L3;
``type_word_report``
    how many goals of the anonymous register have a syntax coordinate moved
    by anonymisation, under the Phase 100 count and under the repaired one --
    mark L4;
``headline``
    the Lean-corpus retrieval figures under the repaired relevance and
    features, set beside the legacy figures taken on the same tree by the
    Phase 100 code (``_data/citation_scope_legacy.json``, a frozen record) --
    marks L5 and L6.

Every count is an integer and every rate a :class:`~fractions.Fraction`
(directive D7); no digest enters any reading (D3).  The Lean half is
``RequestProject/GLM/CitationScope.lean`` (mark L7).
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple

from .. import integrity
from . import citation_reference as cr
from . import lean_address as la
from . import retrieval as rt

__all__ = [
    "STUDY", "LEAN_FILE", "LEGACY_PATH", "DATA_PATH", "infix_type_words",
    "type_word_report", "headline", "legacy_record", "marks",
    "citation_scope_report", "module_digest", "write_measurements",
    "measurements", "state", "current",
]

STUDY = "studies/CITATION_SCOPE_STUDY.md"
LEAN_FILE = "RequestProject/GLM/CitationScope.lean"

_HERE = Path(__file__).resolve()
LEGACY_PATH = _HERE.parent / "_data" / "citation_scope_legacy.json"
DATA_PATH = _HERE.parent / "_data" / "citation_scope.json"

#: The cut-offs the headline reads.
K_LADDER: Tuple[int, ...] = rt.K_LADDER


# ===========================================================================
#  L4 -- the type-word repair
# ===========================================================================

def infix_type_words(text: str) -> Dict[str, int]:
    """The Phase 100 count, kept as the record: a type word anywhere.

    ``Fin`` and ``Set`` were counted only when followed by a space, as the
    shipped map did.
    """
    out = {word: text.count(word) for word in la.TYPE_WORDS}
    out["Fin"] = text.count("Fin ")
    out["Set"] = text.count("Set ")
    return out


def type_word_report() -> Dict[str, object]:
    """Goals of the anonymous register with a syntax coordinate moved."""
    from . import anonymous as an
    names = an.queries()
    texts = {}
    for name in names:
        decl = la.declaration(name)
        texts[name] = rt.strip_declaration_head(decl.statement if decl else "")

    def moved_under(counter) -> Tuple[str, ...]:
        saved = la.type_words
        la.type_words = counter
        try:
            return tuple(name for name in names
                         if an.moved_coordinates(texts[name], exclude=name))
        finally:
            la.type_words = saved

    legacy = moved_under(infix_type_words)
    repaired = moved_under(la.type_words)
    return {"queries": len(names), "moved_legacy": len(legacy),
            "moved_repaired": len(repaired),
            "examples_legacy": legacy[:5], "examples_repaired": repaired[:5]}


# ===========================================================================
#  L5, L6 -- the retrieval figures, re-taken
# ===========================================================================

def headline() -> Dict[str, object]:
    """The Lean-corpus retrieval figures under the shipped readers.

    The same function, run by the Phase 100 code on the same tree, produced
    :data:`LEGACY_PATH`; so the two records differ only in the readers.
    """
    graph = la.citation_graph()
    dq = rt.declaration_query_report()
    gq = rt.goal_query_report()
    sep = la.separation_report()
    neighbours = sep["feature"]["neighbours"]
    injectivity = sep["feature"]["injectivity"]
    return {
        "declarations": len(la.declarations()),
        "tree": la.tree_digest(),
        "edges": sum(len(v) for v in graph.values()),
        "mean_relatives": dq["mean_relatives"],
        "decl": {
            "queries": dq["queries"],
            "chance": dict(dq["chance"]),
            "hits": {s: {k: r[k]["hits"] for k in K_LADDER}
                     for s, r in dq["schemes"].items()},
            "mrr10": {s: r[10]["mrr"] for s, r in dq["schemes"].items()},
        },
        "goal": {
            "queries": gq["queries"],
            "reproduced": gq["features_reproduced"],
            "hits": {s: {k: r[k]["hits"] for k in K_LADDER}
                     for s, r in gq["schemes"].items()},
        },
        "neighbours": {
            "same_file_nearest": neighbours["same_file_nearest"],
            "linked_nearest": neighbours["linked_nearest"],
        },
        "injectivity": {
            "distinct_addresses": injectivity["distinct_addresses"],
            "collision_classes": injectivity["collision_classes"],
            "largest_class_size": injectivity["largest_class_size"],
        },
    }


def _key(value: object) -> object:
    return int(value) if isinstance(value, str) and value.isdigit() else value


def _normalise(value: object) -> object:
    """JSON keys back to ints and fraction strings back to fractions."""
    if isinstance(value, dict):
        return {_key(k): _normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalise(v) for v in value]
    if isinstance(value, str) and "/" in value:
        try:
            return Fraction(value)
        except ValueError:
            return value
    return value


def legacy_record() -> Optional[Dict[str, object]]:
    """The frozen legacy figures (Phase 100 code, same tree), or ``None``."""
    if not LEGACY_PATH.exists():
        return None
    raw = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    return _normalise(raw)            # type: ignore[return-value]


# ===========================================================================
#  The marks
# ===========================================================================

def marks(audit: Mapping[str, Mapping[str, object]],
          words: Mapping[str, object], now: Mapping[str, object],
          legacy: Optional[Mapping[str, object]]) -> Dict[str, bool]:
    """L1 to L6, as declared in the study's §2 (L7 is the Lean file)."""
    old, new = audit["legacy"], audit["scoped"]
    hits = now["decl"]["hits"]                         # type: ignore[index]
    queries = now["decl"]["queries"]                   # type: ignore[index]
    chance = now["decl"]["chance"][5] * queries        # type: ignore[index]
    address = hits["address"][5]
    return {
        "L1": (new["precision"] >= Fraction(95, 100)
               and new["precision"] > old["precision"]),
        "L2": new["one_letter_unconfirmed"] <= 5,
        "L3": new["recall_visible"] >= old["recall_visible"] - Fraction(2, 100),
        "L4": words["moved_repaired"] == 0,
        "L5": (address > hits["digest"][5] and address > hits["shuffled"][5]
               and address > hits["random"][5] and address > chance
               and hits["text"][5] > address),
        "L6": legacy is not None and legacy.get("tree") == now.get("tree"),
    }


def citation_scope_report() -> Dict[str, object]:
    """The whole measurement: audit, type words, headline, legacy, marks."""
    audit = cr.audit_report()
    words = type_word_report()
    now = headline()
    legacy = legacy_record()
    return {
        "reference": audit["state"],
        "constants": audit.get("constants"),
        "audit": {"legacy": audit.get("legacy"), "scoped": audit.get("scoped")},
        "type_words": words,
        "headline": now,
        "legacy": legacy,
        "marks": (marks(audit, words, now, legacy)
                  if "scoped" in audit else {}),
        "study": STUDY,
        "lean_file": LEAN_FILE,
    }


# ===========================================================================
#  The stored measurement
# ===========================================================================

_SOURCES: Tuple[str, ...] = (
    "reasoning/citation_scope.py",
    "reasoning/citation_reference.py",
    "reasoning/lean_address.py",
    "reasoning/retrieval.py",
    "reasoning/anonymous.py",
)


def module_digest() -> str:
    """The measuring code only; the corpus is a dated observation."""
    root = _HERE.parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES
                                  if (root / name).exists()], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def _thaw(value: object) -> object:
    if isinstance(value, dict):
        text = value.get("__fraction__")
        if isinstance(text, str) and len(value) == 1:
            return Fraction(text)
        return {_key(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_thaw(item) for item in value]
    return value


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurement and store it beside its code digest."""
    global _cache
    payload = dict(citation_scope_report())
    payload["source_digest"] = module_digest()
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_freeze(payload), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = _thaw(loaded) if isinstance(loaded, dict) else None   # type: ignore[assignment]
    return _cache


def state() -> Dict[str, object]:
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
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
