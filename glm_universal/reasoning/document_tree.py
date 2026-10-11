"""``glm_universal.reasoning.document_tree`` -- the document tree as a book.

Phase 102 (``studies/DOCUMENT_TREE_STUDY.md``)
----------------------------------------------
Round 9's item N2: whether a third native book for the documents -- a
section's position in the document tree, held as a Golay word -- moves the
document rankings past parity with the raw lexical vector, measured on a
*frozen* copy of the corpus so that the figure does not move with the edit
that reports it.

The document benchmark counts a section relevant to a query exactly when it
is another section of the same document (``corpus.address.relative_table``).
A book holding a section's full position holds its document, and so holds
the relevance relation; the study therefore declares that literal book
(``path``) as the leak control, proves in Lean why it must score perfectly
(``GLM.DocumentTree.separating_key_head``), and asks N2's question of the part
of the tree that does not name the document (``place``: where in its document
a section sits, counted from both ends and capped).

Everything here reads the snapshot ``_data/document_tree_frozen.json``, never
the live documents.  Integers, masks and :class:`~fractions.Fraction` only
(D7); no random source.  The Lean half is
``RequestProject/GLM/DocumentTree.lean``.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..derived import memo
from .. import integrity
from ..substrate.mog import GOLAY
from . import corpus_resample as crs
from . import lean_address as la
from . import native_words as nw
from . import retrieval as rt

__all__ = [
    "FROZEN_PATH", "DATA_PATH", "RANKINGS", "PLACE_CAP",
    "freeze", "frozen", "frozen_state", "path_word", "folder_word",
    "place_word", "place_message", "hamming", "readback_check", "book_check",
    "rank", "census_table", "sample_names", "tally", "discordance",
    "tie_census", "marks", "document_tree_report", "measure",
    "write_measurements", "measurements", "state", "current",
]

STUDY = "studies/DOCUMENT_TREE_STUDY.md"
LEAN_FILE = "RequestProject/GLM/DocumentTree.lean"

FROZEN_PATH = Path(__file__).resolve().parent / "_data" / "document_tree_frozen.json"
DATA_PATH = Path(__file__).resolve().parent / "_data" / "document_tree.json"

#: The cap on a section's ordinal, counted from either end of its document.
PLACE_CAP = 7

K = 5
SAMPLE = 60
ALPHA = Fraction(5, 100)

#: The rankings of the study's §1, each with the line the report prints.
RANKINGS: Tuple[Tuple[str, str], ...] = (
    ("lexical_raw", "the raw lexical vector (the standard)"),
    ("lexical_native2", "lexical book, then structural book (Phase 70)"),
    ("lexical_native3", "lexical book, structural book, then the place word"),
    ("lexical_raw3", "raw lexical, raw structural, raw place (like for like)"),
    ("lexical_place2", "lexical book, then the place word, then structural"),
    ("folder3", "the folder word in the third layer (a partial leak)"),
    ("path3", "the path word in the third layer (the leak)"),
    ("path_first", "the path word first (the leak control)"),
)


# ===========================================================================
#  The snapshot
# ===========================================================================

def _folder(document: str) -> str:
    return document.rsplit("/", 1)[0] if "/" in document else "."


def _canonical(units: Sequence[Mapping[str, object]]) -> str:
    return json.dumps(list(units), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def freeze(path: Optional[Path] = None) -> Path:
    """Take the snapshot from the live corpus.  Refuses a stale address book."""
    from ..corpus import address as ca
    lexical = ca.addresses("lexical")
    structural = ca.addresses("structural")
    if not lexical or not structural:
        raise RuntimeError("the document address book is stale: run "
                           "`corpus --refresh` before freezing")
    vectors = ca.vector_table()
    members: Dict[str, List[str]] = {}
    for unit in ca.units():
        members.setdefault(unit.document, []).append(unit.name)
    rows = []
    for unit in ca.units():
        siblings = members[unit.document]
        rows.append({
            "name": unit.name,
            "document": unit.document,
            "folder": _folder(unit.document),
            "ordinal": siblings.index(unit.name),
            "count": len(siblings),
            "lexical_point": list(lexical[unit.name]),
            "structural_point": list(structural[unit.name]),
            "lexical": list(vectors[unit.name]["lexical"]),
            "structural": list(vectors[unit.name]["structural"]),
        })
    payload = {
        "schema": 1,
        "study": STUDY,
        "units": rows,
        "digest": integrity.sha256_hex(_canonical(rows).encode("utf-8")),
        "live_corpus_digest": _live_corpus_digest(),
    }
    target = Path(path) if path is not None else FROZEN_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=0, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    _frozen_cache.clear()
    return target


def _live_corpus_digest() -> str:
    from ..corpus import inventory as inv
    return inv.corpus_digest()


_frozen_cache: Dict[str, Dict[str, object]] = {}


def frozen() -> Dict[str, object]:
    """The snapshot, its digest verified.  Raises if absent or altered."""
    if "data" in _frozen_cache:
        return _frozen_cache["data"]
    if not FROZEN_PATH.exists():
        raise FileNotFoundError(f"no snapshot at {FROZEN_PATH}; run "
                                "`tools document-tree --freeze`")
    data = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    digest = integrity.sha256_hex(_canonical(data["units"]).encode("utf-8"))
    if digest != data["digest"]:
        raise ValueError("the document-tree snapshot does not match its digest")
    _frozen_cache["data"] = data
    return data


def frozen_state() -> Dict[str, object]:
    """Whether the snapshot is present and intact, and how far the live
    corpus has moved since (a note, never a failure: that is the point)."""
    if not FROZEN_PATH.exists():
        return {"present": False, "intact": False, "moved": None}
    try:
        data = frozen()
    except ValueError:
        return {"present": True, "intact": False, "moved": None}
    return {"present": True, "intact": True, "digest": data["digest"],
            "units": len(data["units"]),
            "moved": data.get("live_corpus_digest") != _live_corpus_digest()}


# ===========================================================================
#  The three tree words
# ===========================================================================

def _documents() -> Tuple[str, ...]:
    return tuple(sorted({u["document"] for u in frozen()["units"]}))


def _folders() -> Tuple[str, ...]:
    return tuple(sorted({u["folder"] for u in frozen()["units"]}))


def path_word(document: str) -> int:
    """The Golay codeword of the document's index: it names the document."""
    return GOLAY.encode_mask(_documents().index(document))


def folder_word(folder: str) -> int:
    """The Golay codeword of the folder's index."""
    return GOLAY.encode_mask(_folders().index(folder))


def place_message(ordinal: int, count: int) -> int:
    """``min(i, 7) + 8 · min(n − 1 − i, 7)``: where a section sits."""
    if not 0 <= ordinal < count:
        raise ValueError("ordinal outside its document")
    return (min(ordinal, PLACE_CAP)
            + (PLACE_CAP + 1) * min(count - 1 - ordinal, PLACE_CAP))


def place_word(ordinal: int, count: int) -> int:
    """The Golay codeword of the place message: no document identity."""
    return GOLAY.encode_mask(place_message(ordinal, count))


def place_raw(ordinal: int, count: int) -> Tuple[int, int]:
    return (min(ordinal, PLACE_CAP), min(count - 1 - ordinal, PLACE_CAP))


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


# ===========================================================================
#  The table every ranking reads
# ===========================================================================

@memo
def _table() -> Tuple[Dict[str, object], ...]:
    out = []
    for u in frozen()["units"]:
        lex_point = tuple(u["lexical_point"])
        str_point = tuple(u["structural_point"])
        out.append({
            "name": u["name"],
            "document": u["document"],
            "lex_point": lex_point,
            "str_point": str_point,
            "lex_rb": rt.readback(lex_point),
            "str_rb": rt.readback(str_point),
            "lex_raw": tuple(u["lexical"]),
            "str_raw": tuple(u["structural"]),
            "place": place_word(u["ordinal"], u["count"]),
            "place_raw": place_raw(u["ordinal"], u["count"]),
            "folder": folder_word(u["folder"]),
            "path": path_word(u["document"]),
        })
    return tuple(out)


def readback_check() -> Dict[str, object]:
    """F1's second half: every snapshot address reads back to its vector."""
    failures = 0
    for row in _table():
        if row["lex_rb"] != row["lex_raw"]:
            failures += 1
        if row["str_rb"] != row["str_raw"]:
            failures += 1
    return {"addresses": 2 * len(_table()), "failures": failures}


def book_check() -> Dict[str, object]:
    """F2: every tree word a codeword, ``path`` injective on documents, and
    every ``place`` word shared by sections of at least two documents."""
    table = _table()
    words = ({row["place"] for row in table} | {row["folder"] for row in table}
             | {row["path"] for row in table})
    non_codewords = sum(1 for w in words if not GOLAY.is_codeword(w))
    path_by_doc: Dict[str, int] = {}
    for row in table:
        path_by_doc[row["document"]] = row["path"]
    injective = len(set(path_by_doc.values())) == len(path_by_doc)
    docs_by_place: Dict[int, set] = {}
    for row in table:
        docs_by_place.setdefault(row["place"], set()).add(row["document"])
    lonely = sorted(w for w, docs in docs_by_place.items() if len(docs) < 2)
    distances = sorted({hamming(a, b) for a in docs_by_place
                        for b in docs_by_place if a != b})
    return {
        "words": len(words),
        "non_codewords": non_codewords,
        "documents": len(path_by_doc),
        "path_injective": injective,
        "place_words": len(docs_by_place),
        "place_words_naming_one_document": len(lonely),
        "least_place_distance": distances[0] if distances else 0,
        "met": non_codewords == 0 and injective and not lonely,
    }


# ===========================================================================
#  The rankings
# ===========================================================================

def _d(a: Sequence[int], b: Sequence[int]) -> int:
    return la.squared_distance(a, b)


def _keys(q: Mapping[str, object], c: Mapping[str, object]
          ) -> Dict[str, Tuple]:
    lex_rb = _d(q["lex_rb"], c["lex_rb"])
    str_rb = _d(q["str_rb"], c["str_rb"])
    str_leech = _d(q["str_point"], c["str_point"])
    lex_raw = _d(q["lex_raw"], c["lex_raw"])
    str_raw = _d(q["str_raw"], c["str_raw"])
    place = hamming(q["place"], c["place"])
    place_l1 = (abs(q["place_raw"][0] - c["place_raw"][0])
                + abs(q["place_raw"][1] - c["place_raw"][1]))
    folder = hamming(q["folder"], c["folder"])
    path = hamming(q["path"], c["path"])
    name = c["name"]
    native2 = (lex_rb, str_rb, str_leech, name)
    return {
        "lexical_raw": (lex_raw, name),
        "lexical_native2": native2,
        "lexical_native3": (lex_rb, str_rb, place, str_leech, name),
        "lexical_raw3": (lex_raw, str_raw, place_l1, name),
        "lexical_place2": (lex_rb, place, str_rb, str_leech, name),
        "folder3": (lex_rb, str_rb, folder, str_leech, name),
        "path3": (lex_rb, str_rb, path, str_leech, name),
        "path_first": (path,) + native2,
    }


def _query_row(index: int, depth: int = K + 1) -> Dict[str, object]:
    """Every ranking's first ``depth`` candidates for one query."""
    table = _table()
    q = table[index]
    keyed: Dict[str, List[Tuple]] = {rid: [] for rid, _ in RANKINGS}
    for j, c in enumerate(table):
        if j == index:
            continue
        for rid, key in _keys(q, c).items():
            keyed[rid].append((key, j))
    out: Dict[str, object] = {}
    for rid, rows in keyed.items():
        rows.sort()
        out[rid] = tuple(j for _, j in rows[:depth])
    # the ceiling of the third layer: do the first two keys of native2 tie
    # across the boundary between rank 5 and rank 6?
    top = out["lexical_native2"]
    if len(top) > K:
        a = _keys(q, table[top[K - 1]])["lexical_native2"][:2]
        b = _keys(q, table[top[K]])["lexical_native2"][:2]
        out["tie_at_boundary"] = a == b
    else:
        out["tie_at_boundary"] = False
    return out


def rank(index: int, ranking: str, k: int = K) -> Tuple[str, ...]:
    """The first ``k`` section names one ranking gives for query ``index``."""
    rows = _query_row(index, depth=max(k, K + 1))
    return tuple(_table()[j]["name"] for j in rows[ranking][:k])


@memo
def census_table() -> Tuple[Dict[str, object], ...]:
    """Every unit of the snapshot as a query, every ranking's first six."""
    return tuple(_query_row(i) for i in range(len(_table())))


def sample_names(size: int = SAMPLE) -> Tuple[int, ...]:
    """The 60-query spread of ``corpus.address.query_sample``, on the snapshot."""
    n = len(_table())
    if size >= n:
        return tuple(range(n))
    step = Fraction(n, size)
    seen: List[int] = []
    for i in range(size):
        index = int(step * i)
        if index < n and index not in seen:
            seen.append(index)
    return tuple(seen)


def _hits(index: int, ranking: str, k: int) -> int:
    table = _table()
    doc = table[index]["document"]
    found = census_table()[index][ranking][:k]
    return sum(1 for j in found if table[j]["document"] == doc)


def tally(indices: Sequence[int]) -> Dict[str, Dict[str, object]]:
    out: Dict[str, Dict[str, object]] = {}
    for rid, _ in RANKINGS:
        hit1 = sum(1 for i in indices if _hits(i, rid, 1))
        hit5 = sum(1 for i in indices if _hits(i, rid, K))
        good = sum(_hits(i, rid, K) for i in indices)
        out[rid] = {"hit@1": hit1, "hit@5": hit5, "relatives@5": good,
                    "precision@5": (Fraction(good, K * len(indices))
                                    if indices else Fraction(0))}
    return out


def discordance(first: str, second: str, indices: Sequence[int]
                ) -> Dict[str, object]:
    """Queries where only ``first`` / only ``second`` has a hit at 5."""
    b = sum(1 for i in indices if _hits(i, first, K) and not _hits(i, second, K))
    c = sum(1 for i in indices if _hits(i, second, K) and not _hits(i, first, K))
    return {"first": first, "second": second, "first_only": b,
            "second_only": c, "sign_test": crs.sign_test(b, c)}


def tie_census() -> Dict[str, object]:
    """How often the third layer can act inside the first five."""
    rows = census_table()
    moved = sum(1 for row in rows
                if set(row["lexical_native3"][:K])
                != set(row["lexical_native2"][:K]))
    return {"queries": len(rows),
            "tie_at_boundary": sum(1 for row in rows if row["tie_at_boundary"]),
            "top5_changed_by_place": moved}


# ===========================================================================
#  The marks
# ===========================================================================

def _at_least(a: Mapping[str, object], b: Mapping[str, object]) -> bool:
    return a["hit@5"] >= b["hit@5"] and a["precision@5"] >= b["precision@5"]


def marks() -> Dict[str, Dict[str, object]]:
    census = tuple(range(len(_table())))
    t = tally(census)
    rb = readback_check()
    books = book_check()
    stored = measurements()
    same = None
    if stored is not None and stored.get("snapshot_digest") == frozen()["digest"]:
        same = (stored.get("census") == _freeze_tally(t))
    disc = discordance("lexical_native3", "lexical_raw", census)
    f4_level = _at_least(t["lexical_native3"], t["lexical_raw"])
    f4_sig = (disc["first_only"] > disc["second_only"]
              and disc["sign_test"] <= ALPHA)
    f4 = "met" if (f4_level and f4_sig) else ("draw" if f4_level else "not met")
    return {
        "F1": {"asks": "snapshot intact, read-back exact, re-taken figures "
                       "equal the stored ones",
               "outcome": ("met" if rb["failures"] == 0 and same is not False
                           else "not met"),
               "readback_failures": rb["failures"],
               "re_taken_equals_stored": same},
        "F2": {"asks": "every tree word a codeword, path injective, no place "
                       "word naming one document",
               "outcome": "met" if books["met"] else "not met"},
        "F3": {"asks": "path_first has a hit at 1 on every census query",
               "outcome": ("met" if t["path_first"]["hit@1"] == len(census)
                           else "not met")},
        "F4": {"asks": "lexical_native3 >= lexical_raw on hit@5 and "
                       "precision@5, discordance its way, sign test <= 0.05",
               "outcome": f4},
        "F5": {"asks": "lexical_native3 >= lexical_raw3 (like for like)",
               "outcome": ("met" if _at_least(t["lexical_native3"],
                                              t["lexical_raw3"])
                           else "not met")},
        "F6": {"asks": "lexical_place2 hit@5 >= lexical_raw",
               "outcome": ("met" if t["lexical_place2"]["hit@5"]
                           >= t["lexical_raw"]["hit@5"] else "not met")},
    }


def _freeze_tally(t: Mapping[str, Mapping[str, object]]) -> object:
    return nw._thaw(nw._freeze(t))


def document_tree_report() -> Dict[str, object]:
    census = tuple(range(len(_table())))
    sample = sample_names()
    return {
        "snapshot_digest": frozen()["digest"],
        "units": len(census),
        "documents": len(_documents()),
        "folders": len(_folders()),
        "census": tally(census),
        "sample": tally(sample),
        "sample_size": len(sample),
        "discordances": {
            "native3_vs_raw": discordance("lexical_native3", "lexical_raw",
                                          census),
            "native3_vs_native2": discordance("lexical_native3",
                                              "lexical_native2", census),
            "native2_vs_raw": discordance("lexical_native2", "lexical_raw",
                                          census),
            "place2_vs_raw": discordance("lexical_place2", "lexical_raw",
                                         census),
            "folder3_vs_native2": discordance("folder3", "lexical_native2",
                                              census),
            "path3_vs_native2": discordance("path3", "lexical_native2",
                                            census),
        },
        "ties": tie_census(),
        "readback": readback_check(),
        "books": book_check(),
        "marks": marks(),
    }


# ===========================================================================
#  The cache, guarded by a digest of the measuring code and of the snapshot
# ===========================================================================

_SOURCES: Tuple[str, ...] = (
    "reasoning/document_tree.py",
    "reasoning/corpus_resample.py",
    "reasoning/retrieval.py",
    "reasoning/lean_address.py",
    "substrate/mog.py",
)


def module_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES
                                  if (root / name).exists()], root)


def measure() -> Dict[str, object]:
    payload = document_tree_report()
    payload["source_digest"] = module_digest()
    return payload


_cache: Optional[Dict[str, object]] = None


def write_measurements(path: Optional[Path] = None) -> Path:
    global _cache
    taken = measure()
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(nw._freeze(taken), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    _cache = None
    return target


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = nw._thaw(loaded) if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent"}
    same = (stored.get("source_digest") == live
            and stored.get("snapshot_digest") == frozen()["digest"])
    return {"present": True, "fresh": same,
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    stored = measurements()
    if stored is None or not state()["fresh"]:
        return None
    return stored
