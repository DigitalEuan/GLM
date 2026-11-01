"""``glm_universal.runtime.sinter`` -- the sintered respelling: the register
lexicon opened once when the corpus respelling refuses a token.

Phase 159 (``studies/THERMO_FRICTION_STUDY.md`` §2.3, experiment C).  The
analogy is sintering: a temporary liquid phase fuses grains, then the body is
solid again.  Here the **solid state** is Phase 157's shipped respelling
(:mod:`glm_universal.runtime.respell`, mode ``loaded``: spelling, then document
count, then use where the count ties) over the corpus vocabulary, and the
liquid phase is a curated lexicon of the registers' own names.

**The register lexicon** (:func:`build_lexicon`).  Every carrier name of the
physics register, the element register (the 118 element names), the interval
register (28) and the comparison classes (45), lower-cased, each whole name
and each of its underscore-separated parts of at least four letters, keeping
only entries made of lower-case letters and underscores.  It is stored in
``runtime/_data/register_lexicon.json`` beside the digest of the code and of
the registers it was read from (:func:`write_lexicon`).  The study's
measurement of record read 726 physics quantities and 1,393 entries in all.

**The protected class.**  A token is **protected** -- never respelt by
sintering -- when it holds a digit, or a capital letter after its first
character (an identifier, a literal, a formula): a protected token is read
exactly as ``loaded`` reads it.  A token **has a word's shape** when it is not
protected and is made of letters and underscores only.

**The sintered reading** (:func:`respell_sintered`).  As ``loaded``, with two
changes:

1. a lexicon entry is a known word (it is never respelt);
2. when ``loaded`` leaves an unknown token unchanged (no corpus candidate, or
   a tie that remains), and the token has a word's shape, the lexicon entries
   one optimal-string-alignment edit from it (lower-cased) are its
   candidates; a unique candidate is taken, replayed on the original's case
   (:func:`glm_universal.runtime.respell.replay`); several, or none, leave it
   unchanged.

So sintering acts only on a token the solid state refused, and returns to the
solid state for the next token: a solid answer is kept whatever the lexicon
holds (``RequestProject/GLM/ThermoFriction.lean``, ``sinter_keeps_solid``,
``sinter_refuses_iff``).  ``GLM.py``'s re-read uses this reading because the
study's marks C1-C4 were met (§7.3: 727 of 735 misspelt register words read
back, ordinary misspellings no worse, no register word respelt, the protected
class read as ``loaded`` reads it).

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/THERMO_FRICTION_STUDY.md
§§1, 2.3, 5, 7 and 7.3, MASTER_PLAN.md Phase 159, the call sites in src/GLM.py
and the Round 11 stand-in
(source_material/Rule30_GLM_Study/rounds/rule30_round11/standins/sinter_standin.py).
The rebuilt lexicon reads 726 physics quantities and 1,393 entries, the
study's figures.*
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Mapping, Optional, Tuple

from .. import integrity
from . import respell as rs

__all__ = [
    "LEXICON_PATH", "MIN_PART", "lexicon", "build_lexicon", "write_lexicon",
    "lexicon_state", "register_names", "protected", "word_shape",
    "known_sintered", "lexicon_candidates", "sinter_token",
    "respell_sintered",
]

_HERE = Path(__file__).resolve()
LEXICON_PATH = rs.DATA_DIRECTORY / "register_lexicon.json"
LEXICON_SCHEMA = 1

#: An underscore-separated part of a name enters the lexicon at this length.
MIN_PART = 4

_ENTRY = re.compile(r"[a-z_]+")
_WORD_SHAPE = re.compile(r"[A-Za-z_]+")


# ===========================================================================
# 1.  THE REGISTER LEXICON
# ===========================================================================

def register_names() -> Dict[str, Tuple[str, ...]]:
    """The names the lexicon is read from, register by register."""
    from ..data_objects import comparison_classes as cc
    from .session import GeometricSession
    session = GeometricSession()
    return {
        "physics": tuple(o.name for o in session.register("physics")),
        "elements": tuple(str(o.attributes.get("name", o.name))
                          for o in session.register("chemistry")),
        "intervals": tuple(o.name for o in session.register("harmonics")),
        "comparison_classes": tuple(c.name for c in cc.COMPARISON_CLASSES),
    }


def _entries(names: Iterable[str]) -> FrozenSet[str]:
    out = set()
    for name in names:
        low = name.lower()
        out.add(low)
        for part in low.split("_"):
            if len(part) >= MIN_PART:
                out.add(part)
    return frozenset(e for e in out if _ENTRY.fullmatch(e))


def _code_digest() -> str:
    return integrity.file_digest(_HERE)


def build_lexicon() -> Dict[str, object]:
    """The lexicon, read from the registers as they now are."""
    names = register_names()
    entries = _entries(n for group in names.values() for n in group)
    registers = integrity.sha256_hex(json.dumps(
        {k: list(v) for k, v in sorted(names.items())},
        sort_keys=True).encode("utf-8"))
    return {
        "schema": LEXICON_SCHEMA,
        "digest": {"code": _code_digest(), "registers": registers},
        "read": {k: len(v) for k, v in names.items()},
        "entries": sorted(entries),
    }


def write_lexicon(path: Optional[Path] = None) -> Path:
    """Read the lexicon from the registers and store it (``runtime/_data``)."""
    payload = build_lexicon()
    target = Path(path or LEXICON_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(f"{target.name}.{os.getpid()}.partial")
    with partial.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=0, sort_keys=False)
        handle.write("\n")
    os.replace(partial, target)
    _LOADED.pop(str(target), None)
    return target


_LOADED: Dict[str, FrozenSet[str]] = {}


def lexicon(path: Optional[Path] = None) -> FrozenSet[str]:
    """The stored lexicon (empty when none is stored: then sintering is the
    solid reading exactly)."""
    target = Path(path or LEXICON_PATH)
    key = str(target)
    if key in _LOADED:
        return _LOADED[key]
    if not target.is_file():
        return frozenset()
    with target.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    out = frozenset(str(e) for e in payload["entries"])
    _LOADED[key] = out
    return out


def lexicon_state(path: Optional[Path] = None) -> Dict[str, object]:
    target = Path(path or LEXICON_PATH)
    if not target.is_file():
        return {"present": False, "verdict": "absent -- take it with "
                "glm_universal.runtime.sinter.write_lexicon()"}
    with target.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    same = payload.get("digest", {}).get("code") == _code_digest()
    return {"present": True, "entries": len(payload.get("entries", ())),
            "read": payload.get("read", {}), "code_current": same,
            "verdict": "present" + ("" if same else
                                    " (taken by another version of sinter.py)")}


# ===========================================================================
# 2.  THE PROTECTED CLASS AND THE SINTERED READING
# ===========================================================================

def protected(token: str) -> bool:
    """A digit anywhere, or a capital letter after the first character."""
    return (any(c.isdigit() for c in token)
            or any(c.isupper() for c in token[1:]))


def word_shape(token: str) -> bool:
    """Not protected, and letters and underscores only."""
    return not protected(token) and bool(_WORD_SHAPE.fullmatch(token))


def known_sintered(token: str, tbl: rs.Table, lex: FrozenSet[str]) -> bool:
    """Known to the corpus vocabulary, or a lexicon entry (change 1)."""
    return rs.known(token, tbl) or token.lower() in lex


def lexicon_candidates(token: str, lex: FrozenSet[str]) -> List[str]:
    """The lexicon entries one optimal-string-alignment edit from the token
    (lower-cased), sorted."""
    low = token.lower()
    return sorted(w for w in set(rs._edits(low)) if w != low and w in lex)


def sinter_token(token: str, company: Iterable[str], tbl: rs.Table,
                 lex: FrozenSet[str]) -> Optional[str]:
    """The sintered reading of one token, or ``None`` when it is left alone."""
    company = list(company)
    if protected(token):
        return rs.respell_token(token, company, "loaded", tbl, amended=True)
    if token.lower() in lex:
        return None
    solid = rs.respell_token(token, company, "loaded", tbl, amended=True)
    if solid is not None:
        return solid
    if not rs.is_candidate(token, tbl, amended=True) or not word_shape(token):
        return None
    found = lexicon_candidates(token, lex)
    if len(found) != 1:
        return None
    return rs.replay(token, found[0])


def respell_sintered(text: str, tbl: Optional[rs.Table] = None,
                     lex: Optional[FrozenSet[str]] = None,
                     company: Optional[Iterable[str]] = None) -> rs.Respelt:
    """The sintered respelling of a question (``mode="sintered"``)."""
    tbl = rs.table() if tbl is None else tbl
    lex = lexicon() if lex is None else lex
    spans = rs.token_spans(text)
    token_list = [t for _s, _e, t in spans]
    given = None if company is None else [w.lower() for w in company]
    replaced: Dict[int, str] = {}
    changes: List[Tuple[str, str]] = []
    for i, tok in enumerate(token_list):
        words = (given if given is not None else
                 [t.lower() for j, t in enumerate(token_list)
                  if j != i and rs.known(t, tbl)])
        new = sinter_token(tok, words, tbl, lex)
        if new is not None and new != tok:
            replaced[i] = new
            changes.append((tok, new))
    return rs.Respelt(original=text, text=rs._rewrite(text, spans, replaced),
                      changes=tuple(changes), mode="sintered")
