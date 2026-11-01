"""``glm_universal.runtime.respell`` -- a did-you-mean read by spelling and by use.

Phase 157 (``studies/FRICTION_TWO_STUDY.md`` §2.1, §2.5, §2.6).  A question the
routed path refuses is respelt once and asked again (``GLM.py``); the respelt
reading is printed only if it answers, so no question that answers can change
(``RequestProject/GLM/FrictionTwo.lean``, ``reread_keeps_answer``).

The rules, as the study fixed them before the measurement:

**The vocabulary.**  The corpus of :mod:`glm_universal.knowledge` (the
project's own text) with the documents whose path names ``friction`` left out
-- those are the stored surveys and the friction studies, whose text *is* the
perturbed questions.  A word is **known** when it occurs in at least
:data:`MIN_DOCUMENTS` documents of that corpus.  The table (each known word's
document count, and for each known alphabetic word of at least four letters
with a word address, its 24 window coordinates of Phase 155,
:func:`glm_universal.knowledge.word_address.vector`) is stored in
``runtime/_data/respell_table.json`` beside the digest of the corpus and of
the code that took it (:func:`write_table`).

**The unknown words.**  A question's tokens are its maximal runs of letters,
digits and underscores; a token is a candidate for respelling when it is at
least :data:`MIN_LENGTH` characters long, holds a letter, and is not known
(compared lower-cased).  Amended (§2.5, T1'): a token holding a digit is a
number, a code or a formula and is never respelt.

**By spelling.**  The candidates for an unknown token are the known words at
one edit from it in the optimal-string-alignment sense: one adjacent
transposition, one deletion, one insertion or one substitution.

**By use.**  ``U(c)`` is the sum, over the question's other known words ``p``
that have coordinates, of the inner product of ``c``'s 24 window coordinates
with ``p``'s.

**The modes** (:data:`MODES`): ``use`` (largest ``U``, then the larger
document count, a remaining tie leaves the token alone); ``spelling`` (the
control: largest document count); ``mismatched`` (the control: ``U`` read from
another question's words, passed as ``company``); and ``loaded`` (§2.6, the
reading ``GLM.py`` ships: the largest document count wins, ``U`` decides only
where the count ties at the top, a remaining tie leaves the token alone).

**The respelt token** (§2.5, T1'): the original with the one edit replayed on
it (:func:`replay`) -- a transposition swaps the original's two characters, a
deletion drops the original's character, an inserted or substituted letter
takes the case of its neighbour on the left -- so every other character keeps
its case.  The first measurement (``amended=False``) respelt digit tokens too
and wrote the lower-cased candidate with the case of the original's first
letter; it is kept for the study's record.

``GLM_RESPELL=0`` turns the re-read off (:func:`enabled`).  Phase 159's
sintered reading, which opens the register lexicon once when this reading
refuses a token, is :mod:`glm_universal.runtime.sinter`; it imports this
module and leaves it unchanged.

Exact and deterministic: every score is an ``int``; nothing samples.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/FRICTION_TWO_STUDY.md
§§1, 2.1, 2.5, 2.6 and 7.1, studies/THERMO_FRICTION_STUDY.md §2.3 and §7
(``respell.replay``), MASTER_PLAN.md Phases 157 and 159, the call sites in
src/GLM.py and the Round 11 stand-in
(source_material/Rule30_GLM_Study/rounds/rule30_round11/standins/respell_standin.py).
The stored table is re-derived by :func:`write_table` from the corpus as it
now is; its digest records which corpus that was.*

*Last altered 31 October 2026 (repository check): the separate left-out path
prefix is gone; which files are read is decided by the knowledge reader's walk
alone (the derived table is unchanged).*
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .. import integrity

__all__ = [
    "MODES", "SHIPPED_MODE", "MIN_DOCUMENTS", "MIN_LENGTH", "TABLE_PATH",
    "ENVIRONMENT", "Table", "Respelt", "enabled", "table", "build_table",
    "write_table", "table_state", "tokens", "token_spans", "known",
    "is_candidate", "candidates", "edit", "use_score", "choose", "replay",
    "first_letter_case", "respell", "respell_token", "code_digest",
]

#: The four readings of Phase 157; ``loaded`` is the one ``GLM.py`` ships.
MODES: Tuple[str, ...] = ("use", "spelling", "mismatched", "loaded")

#: The reading the re-read in ``GLM.py`` uses (§2.6).
SHIPPED_MODE = "loaded"

#: A word is known when at least this many documents of the vocabulary hold it.
MIN_DOCUMENTS = 3

#: A token shorter than this is never respelt.
MIN_LENGTH = 4

#: A known word gets coordinates only when it is alphabetic and this long.
COORDINATE_MIN_LENGTH = 4

#: ``GLM_RESPELL=0`` switches the re-read off.
ENVIRONMENT = "GLM_RESPELL"

#: The path fragment that leaves a document out of the vocabulary (§2.1).
LEFT_OUT = "friction"

_HERE = Path(__file__).resolve()
DATA_DIRECTORY = _HERE.parent / "_data"
TABLE_PATH = DATA_DIRECTORY / "respell_table.json"
TABLE_SCHEMA = 1

_TOKEN = re.compile(r"[A-Za-z0-9_]+")
_VOCABULARY_WORD = re.compile(r"[a-z0-9_]+")
_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789_"


def enabled(environ: Mapping[str, str] = os.environ) -> bool:
    """Whether the re-read of a refused question runs (``GLM_RESPELL`` unset
    or anything but ``0``)."""
    return environ.get(ENVIRONMENT, "").strip() != "0"


# ===========================================================================
# 1.  THE TABLE
# ===========================================================================

@dataclass(frozen=True)
class Table:
    """The vocabulary: each known word's document count, and the window
    coordinates of the known alphabetic words that have a word address."""

    documents: Mapping[str, int]
    coordinates: Mapping[str, Tuple[int, ...]]
    digest: Mapping[str, str] = field(default_factory=dict)
    present: bool = True

    def count(self, word: str) -> int:
        return self.documents.get(word, 0)


_EMPTY = Table(documents={}, coordinates={}, digest={}, present=False)
_LOADED: Dict[str, Table] = {}


def code_digest() -> str:
    """The digest of this module's source (the code that takes the table)."""
    return integrity.file_digest(_HERE)


def _vocabulary_documents(knowledge) -> tuple:
    out = []
    for document in knowledge.documents:
        path = document.path
        if LEFT_OUT in path.lower():
            continue
        out.append(document)
    return tuple(out)


def build_table(knowledge=None) -> Dict[str, object]:
    """The table, read off the knowledge corpus as it now is (§2.1).

    Counts the vocabulary corpus (the knowledge corpus less every document
    whose path names ``friction``), keeps the words in at least
    :data:`MIN_DOCUMENTS` documents, and gives each known alphabetic word of
    at least four letters that has a word address (a context set, as
    :func:`glm_universal.knowledge.word_address.address_book` reads it) its
    24 window coordinates against the vocabulary corpus's own anchors.
    """
    from ..knowledge import model as mdl
    from ..knowledge import word_address as wa
    knowledge = mdl.load() if knowledge is None else knowledge
    documents = _vocabulary_documents(knowledge)
    model = mdl.train(documents)
    contexts = mdl.context_sets(model)
    known = {w: n for w, n in model.df.items()
             if n >= MIN_DOCUMENTS and _VOCABULARY_WORD.fullmatch(w)}
    anchor_words = wa.anchors(model, "window")
    coordinates = {}
    for w in sorted(contexts):
        if w in known and w.isalpha() and len(w) >= COORDINATE_MIN_LENGTH:
            coordinates[w] = list(wa.vector(model, w, anchor_words, "window"))
    corpus = integrity.sha256_hex("".join(
        f"{d.path}={d.digest};" for d in documents).encode("utf-8"))
    return {
        "schema": TABLE_SCHEMA,
        "digest": {"corpus": corpus, "code": code_digest(),
                   "knowledge": knowledge.digest},
        "documents_read": len(documents),
        "documents_left_out": len(knowledge.documents) - len(documents),
        "min_documents": MIN_DOCUMENTS,
        "anchors": list(anchor_words),
        "known": dict(sorted(known.items())),
        "coordinates": coordinates,
    }


def write_table(knowledge=None, path: Optional[Path] = None) -> Path:
    """Take the table from the corpus and store it (``runtime/_data``)."""
    payload = build_table(knowledge)
    target = Path(path or TABLE_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(f"{target.name}.{os.getpid()}.partial")
    with partial.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"), sort_keys=False)
        handle.write("\n")
    os.replace(partial, target)
    _LOADED.pop(str(target), None)
    return target


def table(path: Optional[Path] = None) -> Table:
    """The stored table (an empty, absent table when none is stored: then
    nothing is known, nothing has a candidate and nothing is respelt)."""
    target = Path(path or TABLE_PATH)
    key = str(target)
    if key in _LOADED:
        return _LOADED[key]
    if not target.is_file():
        return _EMPTY
    with target.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    out = Table(documents={str(w): int(n) for w, n in payload["known"].items()},
                coordinates={str(w): tuple(int(x) for x in v)
                             for w, v in payload["coordinates"].items()},
                digest=dict(payload.get("digest", {})), present=True)
    _LOADED[key] = out
    return out


def table_state(path: Optional[Path] = None) -> Dict[str, object]:
    """Whether a table is stored, and whether the code that took it is this
    module as it now is (the corpus digest moves with every edit to the
    project's text and is reported, not enforced)."""
    t = table(path)
    if not t.present:
        return {"present": False, "verdict": "absent -- take it with "
                "glm_universal.runtime.respell.write_table()"}
    same_code = t.digest.get("code") == code_digest()
    return {"present": True, "known": len(t.documents),
            "with_coordinates": len(t.coordinates),
            "code_current": same_code, "digest": dict(t.digest),
            "verdict": "present" + ("" if same_code else
                                    " (taken by another version of respell.py)")}


# ===========================================================================
# 2.  TOKENS, CANDIDATES AND THE EDIT
# ===========================================================================

def token_spans(text: str) -> List[Tuple[int, int, str]]:
    """``(start, end, token)`` for every maximal run of letters, digits and
    underscores."""
    return [(m.start(), m.end(), m.group(0)) for m in _TOKEN.finditer(text)]


def tokens(text: str) -> List[str]:
    return [t for _s, _e, t in token_spans(text)]


def known(word: str, tbl: Optional[Table] = None) -> bool:
    tbl = table() if tbl is None else tbl
    return tbl.count(word.lower()) >= MIN_DOCUMENTS


def is_candidate(token: str, tbl: Optional[Table] = None,
                 amended: bool = True) -> bool:
    """Whether ``token`` is respelt at all: long enough, holding a letter,
    unknown, and (amended) holding no digit."""
    if len(token) < MIN_LENGTH or not any(c.isalpha() for c in token):
        return False
    if amended and any(c.isdigit() for c in token):
        return False
    return not known(token, tbl)


def _edits(word: str) -> Iterable[str]:
    n = len(word)
    for i in range(n):
        yield word[:i] + word[i + 1:]
    for i in range(n - 1):
        if word[i] != word[i + 1]:
            yield word[:i] + word[i + 1] + word[i] + word[i + 2:]
    for i in range(n):
        for c in _ALPHABET:
            if c != word[i]:
                yield word[:i] + c + word[i + 1:]
    for i in range(n + 1):
        for c in _ALPHABET:
            yield word[:i] + c + word[i:]


def candidates(token: str, tbl: Optional[Table] = None) -> List[str]:
    """The known words one optimal-string-alignment edit from ``token``
    (lower-cased), sorted."""
    tbl = table() if tbl is None else tbl
    low = token.lower()
    return sorted({w for w in _edits(low)
                   if w != low and tbl.count(w) >= MIN_DOCUMENTS})


def edit(source: str, target: str) -> Optional[Tuple[str, int]]:
    """The one edit taking ``source`` to ``target`` (both compared as given):
    ``("transpose", i)``, ``("substitute", i)``, ``("delete", i)`` or
    ``("insert", i)``, the first position at which it applies; ``None`` when
    they are not one edit apart."""
    a, b = source, target
    if a == b:
        return None
    if len(a) == len(b):
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        if len(diff) == 1:
            return ("substitute", diff[0])
        if (len(diff) == 2 and diff[1] == diff[0] + 1
                and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]):
            return ("transpose", diff[0])
        return None
    if len(a) == len(b) + 1:
        for i in range(len(a)):
            if a[:i] + a[i + 1:] == b:
                return ("delete", i)
        return None
    if len(b) == len(a) + 1:
        for i in range(len(b)):
            if b[:i] + b[i + 1:] == a:
                return ("insert", i)
        return None
    return None


def _cased_like(c: str, model: str) -> str:
    return c.upper() if model.isupper() else c.lower()


def replay(original: str, candidate: str) -> str:
    """The candidate written on the original's case: the one edit from the
    lower-cased original to ``candidate`` replayed on the original itself
    (§2.5).  An inserted or substituted letter takes the case of its
    neighbour on the left (the character it replaces, at position 0)."""
    op = edit(original.lower(), candidate)
    if op is None:
        return candidate
    kind, i = op
    if kind == "transpose":
        return original[:i] + original[i + 1] + original[i] + original[i + 2:]
    if kind == "delete":
        return original[:i] + original[i + 1:]
    if kind == "substitute":
        model = original[i - 1] if i > 0 else original[i]
        return original[:i] + _cased_like(candidate[i], model) + original[i + 1:]
    model = original[i - 1] if i > 0 else (original[0] if original else "")
    return original[:i] + _cased_like(candidate[i], model) + original[i:]


def first_letter_case(original: str, candidate: str) -> str:
    """The first measurement's writing (§2.1): the lower-cased candidate with
    the case of the original's first letter."""
    if original and candidate and original[0].isupper():
        return candidate[0].upper() + candidate[1:]
    return candidate


# ===========================================================================
# 3.  THE READINGS
# ===========================================================================

def use_score(candidate: str, company: Iterable[str],
              tbl: Optional[Table] = None) -> int:
    """``U(c)``: the inner products of ``c``'s window coordinates with those
    of each distinct known word of the company that has coordinates."""
    tbl = table() if tbl is None else tbl
    mine = tbl.coordinates.get(candidate)
    if mine is None:
        return 0
    total = 0
    for p in sorted(set(w.lower() for w in company)):
        if p == candidate:
            continue
        theirs = tbl.coordinates.get(p)
        if theirs is not None:
            total += sum(x * y for x, y in zip(mine, theirs))
    return total


def _unique_best(scored: Sequence[Tuple[Tuple[int, ...], str]]) -> Optional[str]:
    if not scored:
        return None
    best = max(s for s, _ in scored)
    top = [w for s, w in scored if s == best]
    return top[0] if len(top) == 1 else None


def choose(cands: Sequence[str], company: Iterable[str], mode: str,
           tbl: Optional[Table] = None) -> Optional[str]:
    """The candidate a mode takes, or ``None`` (no candidate, or a tie that
    remains)."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    tbl = table() if tbl is None else tbl
    company = list(company)
    if mode == "spelling":
        return _unique_best([((tbl.count(c),), c) for c in cands])
    if mode == "loaded":
        return _unique_best([((tbl.count(c), use_score(c, company, tbl)), c)
                             for c in cands])
    # "use" and "mismatched" differ only in the company they are given.
    return _unique_best([((use_score(c, company, tbl), tbl.count(c)), c)
                         for c in cands])


def _own_company(token_list: Sequence[str], index: int,
                 tbl: Table) -> List[str]:
    return [t.lower() for j, t in enumerate(token_list)
            if j != index and known(t, tbl)]


def respell_token(token: str, company: Iterable[str], mode: str = SHIPPED_MODE,
                  tbl: Optional[Table] = None, amended: bool = True
                  ) -> Optional[str]:
    """The respelt token, or ``None`` when the reading leaves it alone."""
    tbl = table() if tbl is None else tbl
    if not is_candidate(token, tbl, amended):
        return None
    chosen = choose(candidates(token, tbl), company, mode, tbl)
    if chosen is None:
        return None
    return replay(token, chosen) if amended else first_letter_case(token, chosen)


@dataclass(frozen=True)
class Respelt:
    """A question respelt: the text, and every token changed."""

    original: str
    text: str
    changes: Tuple[Tuple[str, str], ...] = ()
    mode: str = SHIPPED_MODE

    @property
    def changed(self) -> bool:
        return self.text != self.original

    def note(self) -> str:
        """``'dsecribe' read as 'describe'`` (the ``RESPELT`` line)."""
        return ", ".join(f"{old!r} read as {new!r}" for old, new in self.changes)


def _rewrite(text: str, spans: Sequence[Tuple[int, int, str]],
             replaced: Mapping[int, str]) -> str:
    out: List[str] = []
    last = 0
    for i, (start, end, _tok) in enumerate(spans):
        if i in replaced:
            out.append(text[last:start])
            out.append(replaced[i])
            last = end
    out.append(text[last:])
    return "".join(out)


def respell(text: str, mode: str = SHIPPED_MODE,
            company: Optional[Iterable[str]] = None,
            tbl: Optional[Table] = None, amended: bool = True) -> Respelt:
    """Respell every unknown token of ``text`` that has a candidate.

    ``company`` replaces the question's own known words as the words ``U`` is
    read from (the mismatched control passes another question's words); by
    default each token's company is the question's other known words.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    tbl = table() if tbl is None else tbl
    spans = token_spans(text)
    token_list = [t for _s, _e, t in spans]
    replaced: Dict[int, str] = {}
    changes: List[Tuple[str, str]] = []
    given = None if company is None else [w.lower() for w in company]
    for i, tok in enumerate(token_list):
        words = given if given is not None else _own_company(token_list, i, tbl)
        new = respell_token(tok, words, mode, tbl, amended)
        if new is not None and new != tok:
            replaced[i] = new
            changes.append((tok, new))
    return Respelt(original=text, text=_rewrite(text, spans, replaced),
                   changes=tuple(changes), mode=mode)
