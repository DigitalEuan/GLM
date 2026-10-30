"""``glm_universal.knowledge.study`` -- the corpus-knowledge measurement.

The measurement of ``CORPUS_KNOWLEDGE_STUDY.md``: the corpus read by rule
into folder, document, paragraph, sentence and token, with the
co-occurrence model, the next-token baseline, and the word-place-on-the-
lattice experiment.

*Reconstructed 29 October 2026 (Iteration 2, extended Iteration 4).  The
original ``study.py`` was lost in the upload; this version exposes the
two names ``word_address.py`` imports (``NUMBER_WORDS`` and
``plural_pairs``) plus the standard 8-function study apparatus
(``compute``/``measure``/``write_measurements``/``state``/``current``/
``module_digest``/``corpus_knowledge_report``) so the CLI subcommand
``corpus-knowledge`` and the tier-0 contract work.  The stored
measurement JSON does not exist, so the report returns ``available=False``;
re-take it with ``python3 -m glm_universal.tools corpus-knowledge --write``
once the full session infrastructure is restored.*
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .. import integrity

__all__ = [
    "NUMBER_WORDS", "plural_pairs",
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest",
    "corpus_knowledge_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "corpus_knowledge.json"

#: Files whose digest ``module_digest`` covers.
_SOURCES: Tuple[str, ...] = (
    "knowledge/study.py",
    "knowledge/model.py",
    "knowledge/reader.py",
    "knowledge/answer.py",
)

_cache: Optional[Dict[str, object]] = None


#: The number words the corpus-knowledge study grades (per
#: CORPUS_KNOWLEDGE_STUDY.md: "words used like *seven*: *eight, ten, four,
#: nine, five, six, …*").  These are the English cardinal number words the
#: corpus's next-token baseline is graded against.
NUMBER_WORDS: Tuple[str, ...] = (
    "zero", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
    "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "million", "billion",
)


def plural_pairs(knowledge: Any) -> List[Tuple[str, str]]:
    """The (singular, plural) pairs the corpus's number-word neighbours
    are graded against.

    *This is a working stub.*  The full implementation would scan the
    corpus's vocabulary for ``(word, word + "s")`` pairs where both forms
    appear with sufficient frequency, and return them as the
    co-occurrence neighbours of the number words.  The stub returns an
    empty list; ``word_address.compute`` degrades gracefully (no
    plural-pair neighbours are added to the address book).
    """
    return []


# ---------------------------------------------------------------------------
# Standard 8-function study apparatus (added Iteration 4)
# ---------------------------------------------------------------------------

def _plain(x: Any) -> Any:
    """Recursive serializer: Fraction -> str, dict/list -> plain."""
    from fractions import Fraction
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def compute(knowledge: Any = None) -> Dict[str, object]:
    """Run the corpus-knowledge measurement and return the report dict.

    *Working stub.*  Returns the report dict shape with all marks
    ``False``, so the stored JSON (when it exists) carries the true marks.
    """
    marks: Dict[str, bool] = {m: False for m in (
        "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9",
    )}
    return {
        "documents": 0,
        "sentences": 0,
        "tokens": 0,
        "next_token": {"correct": 0, "novel": 0, "control": 0},
        "number_words": {},
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }


def module_digest() -> str:
    """The digest of every file in :data:`_SOURCES`."""
    root = _HERE.parent  # glm_universal/
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    """``compute()`` plus the ``source_digest``."""
    r = compute()
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None) -> Path:
    """Write ``measure()`` as JSON to :data:`DATA_PATH` (or ``path``)."""
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure()), indent=1, sort_keys=True,
                       ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """Read the stored measurement from :data:`DATA_PATH`, or ``None``."""
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
    """``{"present", "fresh", "verdict", "live_digest", "stored_digest"}``."""
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
    """``measurements()`` if fresh, else ``None``."""
    if state()["fresh"]:
        return measurements()
    return None


def corpus_knowledge_report() -> Dict[str, object]:
    """If fresh: the stored measurement with ``available=True``.  Else: a
    reason and the command to re-take it."""
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    return {
        "available": False,
        "reason": ("the stored measurement is absent; re-take it with "
                   "python3 -m glm_universal.tools corpus-knowledge --write"),
    }
