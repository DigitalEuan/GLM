"""``glm_universal.knowledge.definitions_study`` -- the measurement of Phase 155.

``studies/CORPUS_DEFINITIONS_STUDY.md``: ``corpus define`` graded against the
held-out glossary of the paper (:mod:`~glm_universal.knowledge.glossary`) --
G1-G4 under define's own (pattern) ranking and the amended G1'-G4' under the
context ranking -- and a word's place on the Leech lattice
(:mod:`~glm_universal.knowledge.word_address`) -- W1-W4 under the window
scheme and the amended W2', W3' under the positional scheme.  8 marks and 6
amended marks.

:func:`compute` takes the measurement from the corpus as it now is (a minute
or two: two address books and 54 graded definitions).  Nothing here writes:
the stored measurement (``_data/corpus_definitions.json``) is written only by
``tools corpus-definitions --write``, and :func:`corpus_definitions_report`
reports it absent or stale when it is.

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation (the 29 October placeholder returned every
mark false); rebuilt from studies/CORPUS_DEFINITIONS_STUDY.md §§2 and 7,
MASTER_PLAN.md Phase 155 and the report shape read by tools.py
``_corpus_definitions``.*
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest", "corpus_definitions_report",

]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "corpus_definitions.json"


_SOURCES: Tuple[str, ...] = (
    "knowledge/definitions_study.py",
    "knowledge/answer.py",
    "knowledge/glossary.py",
    "knowledge/word_address.py",
    "knowledge/model.py",
    "knowledge/reader.py",
    "knowledge/study.py",
)

_cache: Optional[Dict[str, object]] = None


def _plain(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def compute(knowledge: Any = None) -> Dict[str, object]:
    """Take the Phase 155 measurement from the corpus as it now is."""
    from . import glossary as gl
    from . import model as mdl
    from . import word_address as wa
    knowledge = mdl.load() if knowledge is None else knowledge
    removed = gl.held_out_ids(knowledge)
    held = gl.hold_out(knowledge)
    graded = gl.grade_definitions(held, "pattern")
    graded_context = gl.grade_definitions(held, "context")
    words = wa.compute(knowledge, "window")
    words_positional = wa.compute(knowledge, "positional")
    g = gl.marks(graded)
    gc = gl.marks(graded_context)
    marks: Dict[str, bool] = {
        "G1": g["G1"], "G2": g["G2"], "G3": g["G3"], "G4": g["G4"],
        "W1": words["marks"]["W1"], "W2": words["marks"]["W2"],
        "W3": words["marks"]["W3"], "W4": words["marks"]["W4"],
    }
    amended: Dict[str, bool] = {
        "G1'": gc["G1"], "G2'": gc["G2"], "G3'": gc["G3"], "G4'": gc["G4"],
        "W2'": words_positional["marks"]["W2"], "W3'": words_positional["marks"]["W3"],
    }
    return {
        "corpus": {"documents": len(knowledge.documents),
                   "sentences": len(knowledge.sentences),
                   "digest": knowledge.digest},
        "glossary": {"terms": len(gl.GLOSSARY), "held_out": len(removed),
                     "held_out_addresses": [knowledge.sentences[i].address
                                            for i in removed],
                     "leaks": graded["leaks"] + graded_context["leaks"]},
        "graded": graded,
        "graded_context": graded_context,
        "words": words,
        "words_positional": words_positional,
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
        "amended": amended,
        "amended_met": sum(1 for v in amended.values() if v),
        "amended_taken": len(amended),
    }


def module_digest() -> str:
    root = _HERE.parent  # glm_universal/
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    r = compute()
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None) -> Path:
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure()), indent=1, sort_keys=True,
                      ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    try:
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _cache = None
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    stored_digest = stored.get("source_digest")
    return {"present": True, "fresh": stored_digest == live,
            "verdict": "current" if stored_digest == live else "stale",
            "live_digest": live, "stored_digest": stored_digest}


def current() -> Optional[Dict[str, object]]:
    if state()["fresh"]:
        return measurements()
    return None


def corpus_definitions_report() -> Dict[str, object]:
    """If fresh: the stored measurement with ``available=True``.  Else: why
    not (absent or stale) and the command that re-takes it; the live
    figures are :func:`compute`'s."""
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    verdict = state()["verdict"]
    return {
        "available": False,
        "verdict": verdict,
        "reason": (f"the stored measurement is {verdict}; re-take it with "
                   f"python3 -m glm_universal.tools corpus-definitions --write"),
    }
