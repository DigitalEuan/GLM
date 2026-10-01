"""``glm_universal.reasoning.native_words`` -- word overlap on Golay words.

Phase 71 (``studies/NATIVE_WORDS_STUDY.md``)
--------------------------------------------
Phase 70's ledger left two rows as capacity results: the standard word-overlap
ranking stays far ahead of every lexical Leech address, on the Lean corpus and
on the documents.  The refinement the owner's instruction points at is a
*native word ranking* -- the overlap computed on Golay words of the tokens
rather than on the tokens.  This module is that ranking and its measurement.

The objects (the study's §1)
----------------------------
``letter_word(part)``
    the 24-bit mask of a part's letters under the lexical book's stated
    folding (``a``..``x`` keep their bucket, ``y`` and ``z`` join ``a`` and
    ``b``): a point of the Golay code's ambient space, read bit by bit.
``token_parts(token)``
    a token split at ``_``, ``.``, ``'`` and digits.
``golay_class(word)``
    the set of nearest codewords of a letter word, from the complete syndrome
    decoder: one inside the packing radius, six at coset weight 4.  No tie is
    broken.
``NameBook``
    the Golay name of a token: its whole letter word and its index among the
    vocabulary's tokens with that word.  Injective by construction, so the
    overlap of names *is* the token overlap (``GLM.NativeWords.jaccard_image``).

The rankings (the study's §2) are lexicographic keys over these, with the
Leech distance and the name as the last two layers.  Everything is an integer,
a mask or a :class:`~fractions.Fraction` (D7); no digest is in any key (D3).
The Lean half is ``RequestProject/GLM/NativeWords.lean``.
"""

from __future__ import annotations

import json
import re
from fractions import Fraction
from pathlib import Path
from typing import (Callable, Dict, FrozenSet, Iterable, List, Mapping,
                    Optional, Sequence, Tuple)

from ..derived import memo
from .. import integrity
from ..substrate import golay_decode as gd
from . import lean_address as la
from . import retrieval as rt

__all__ = [
    "letter_word", "token_parts", "golay_class", "NameBook",
    "Profile", "profile", "jaccard", "RANKINGS", "rank_profiles",
    "rank_lean", "rank_documents", "lean_report", "document_report",
    "native_words_report", "tool_summary", "module_digest", "corpus_digest", "corpus_drift", "measure",
    "write_measurements", "measurements", "state", "current", "DATA_PATH",
]

STUDY = "studies/NATIVE_WORDS_STUDY.md"
LEAN_FILE = "RequestProject/GLM/NativeWords.lean"


# ===========================================================================
#  The objects
# ===========================================================================

def letter_word(part: str) -> int:
    """The 24-bit mask of the letter buckets a part uses."""
    mask = 0
    for char in part.lower():
        if "a" <= char <= "z":
            mask |= 1 << ((ord(char) - ord("a")) % rt.LEXICAL_BUCKETS)
    return mask


_SPLIT = re.compile(r"[_.'0-9]+")


def token_parts(token: str) -> Tuple[str, ...]:
    """A token split at ``_``, ``.``, ``'`` and digits; empty parts dropped."""
    return tuple(part for part in _SPLIT.split(token.lower()) if part)


_CLASS_CACHE: Dict[int, FrozenSet[int]] = {}


def golay_class(word: int) -> FrozenSet[int]:
    """Every nearest codeword of a 24-bit word: one, or six at coset weight 4."""
    found = _CLASS_CACHE.get(word)
    if found is None:
        found = frozenset(gd.decode_complete(word).candidates)
        _CLASS_CACHE[word] = found
    return found


class NameBook:
    """The Golay names of one vocabulary.

    A name is ``(letter_word(token), index)``, the index counting the
    vocabulary's tokens with the same letter word in sorted order.  A token
    outside the vocabulary is named after every vocabulary token with its
    word, in the order it is first asked for, so two new tokens never share a
    name either: the book stays injective on everything it has named.
    """

    def __init__(self, vocabulary: Iterable[str]):
        by_word: Dict[int, List[str]] = {}
        for token in sorted(set(vocabulary)):
            by_word.setdefault(letter_word(token), []).append(token)
        self._names: Dict[str, Tuple[int, int]] = {}
        self._next: Dict[int, int] = {}
        for word, tokens in by_word.items():
            for index, token in enumerate(tokens):
                self._names[token] = (word, index)
            self._next[word] = len(tokens)
        self.vocabulary_size = len(self._names)

    def name(self, token: str) -> Tuple[int, int]:
        found = self._names.get(token)
        if found is None:
            word = letter_word(token)
            found = (word, self._next.get(word, 0))
            self._next[word] = found[1] + 1
            self._names[token] = found
        return found

    def injective(self) -> bool:
        """No two tokens named so far share a name."""
        return len(set(self._names.values())) == len(self._names)


class Profile:
    """The three native sets of one text, and its token set for the standard."""

    __slots__ = ("tokens", "names", "parts", "letters", "classes")

    def __init__(self, tokens: FrozenSet[str], book: NameBook):
        self.tokens = tokens
        self.names = frozenset(book.name(t) for t in tokens)
        letters = set()
        parts = set()
        for token in tokens:
            for part in token_parts(token):
                word = letter_word(part)
                if word:
                    letters.add(word)
                    parts.add(part)
        self.parts = frozenset(parts)
        self.letters = frozenset(letters)
        classes: set = set()
        for word in self.letters:
            classes |= golay_class(word)
        self.classes = frozenset(classes)


def profile(tokens: FrozenSet[str], book: NameBook) -> Profile:
    return Profile(tokens, book)


def jaccard(a: FrozenSet, b: FrozenSet) -> Fraction:
    """``|a & b| / |a | b|``, and 0 on two empty sets."""
    union = len(a | b)
    return Fraction(len(a & b), union) if union else Fraction(0)


# ===========================================================================
#  The rankings
# ===========================================================================

#: Each ranking's key layers, in order; the name is always the last layer.
RANKINGS: Dict[str, Tuple[str, ...]] = {
    "text": ("tokens",),
    "text_leech": ("tokens", "leech"),
    "words_native": ("names", "letters", "classes", "leech"),
    "letters": ("letters", "classes", "leech"),
    "classes": ("classes", "leech"),
    # Post-hoc like-for-like controls (the study's §3.3): the same keys with
    # the parts themselves as strings in place of their Golay letter words.
    "parts": ("parts", "leech"),
    "text_parts": ("tokens", "parts", "leech"),
}

#: The rankings the declared marks read; the rest are reported beside them.
DECLARED: Tuple[str, ...] = ("text", "text_leech", "words_native", "letters",
                             "classes")


def rank_profiles(scheme: str, query: Profile, table: Mapping[str, Profile],
                  names: Sequence[str], k: int, exclude: Optional[str],
                  leech: Callable[[str], int]) -> Tuple[Tuple[str, Fraction], ...]:
    """The top ``k`` of ``names`` under one ranking, with each first-layer value.

    The Leech distance is asked for only when a key uses it.
    """
    layers = RANKINGS[scheme]
    scored = []
    for name in names:
        if name == exclude:
            continue
        other = table[name]
        key: List[object] = []
        for layer in layers:
            if layer == "leech":
                key.append(leech(name))
            else:
                key.append(-jaccard(getattr(query, layer), getattr(other, layer)))
        key.append(name)
        scored.append(tuple(key))
    scored.sort()
    return tuple((row[-1], -row[0]) for row in scored[:k])


# ===========================================================================
#  The Lean corpus
# ===========================================================================

@memo
def lean_book() -> NameBook:
    vocabulary = set()
    for tokens in rt.statement_tokens().values():
        vocabulary |= tokens
    return NameBook(vocabulary)


@memo
def lean_profiles() -> Dict[str, Profile]:
    book = lean_book()
    return {name: Profile(tokens, book)
            for name, tokens in rt.statement_tokens().items()}


def rank_lean(text: str, k: int = rt.K_DEFAULT, scheme: str = "words_native",
              exclude: Optional[str] = None,
              point: Optional[Sequence[int]] = None
              ) -> Tuple[rt.Candidate, ...]:
    """A native word ranking of the Lean corpus for a fragment of Lean.

    ``point`` is the query's structural Leech address; when it is not given
    it is decoded live from the text (:func:`retrieval.goal_address`).
    """
    table = lean_profiles()
    query = Profile(rt.identifier_tokens(text), lean_book())
    addresses = rt._point_table("address")
    if point is None and "leech" in RANKINGS[scheme]:
        point = rt.goal_address(text, exclude=exclude)
    names = tuple(n for n in rt.corpus() if n in table)

    def leech(name: str) -> int:
        other = addresses.get(name)
        if point is None or other is None:
            return 0
        return la.squared_distance(point, other)

    files = rt.file_of()
    found = rank_profiles(scheme, query, table, names, k, exclude, leech)
    return tuple(rt.Candidate(name=name, file=files.get(name, ""),
                              score=value, metric="overlap")
                 for name, value in found)


# ===========================================================================
#  The document corpus
# ===========================================================================

def _documents():
    # The corpus layer sits above the reasoning layer and imports it.
    from ..corpus import address as ad
    return ad


@memo
def document_book() -> NameBook:
    ad = _documents()
    vocabulary = set()
    for tokens in ad.token_table().values():
        vocabulary |= tokens
    return NameBook(vocabulary)


@memo
def document_profiles() -> Dict[str, Profile]:
    book = document_book()
    return {name: Profile(tokens, book)
            for name, tokens in _documents().token_table().items()}


def rank_documents(query: str, k: int = 5, scheme: str = "words_native",
                   exclude: str = "") -> Tuple[Tuple[str, Fraction], ...]:
    """A native word ranking of the document corpus: ``(section, overlap)``."""
    ad = _documents()
    table = document_profiles()
    profile_q = Profile(ad.distinctive_words(query), document_book())
    addresses = ad.addresses("lexical")
    point = (la.quantise(ad.lexical_vector(query))
             if "leech" in RANKINGS[scheme] else None)
    names = tuple(unit.name for unit in ad.units())

    def leech(name: str) -> int:
        other = addresses.get(name)
        if point is None or other is None:
            return 0
        return la.squared_distance(point, other)

    return rank_profiles(scheme, profile_q, table, names, k, exclude or None,
                         leech)


# ===========================================================================
#  Measurement
# ===========================================================================

def _tally(rows: Sequence[Tuple[Sequence[str], FrozenSet[str]]]
           ) -> Dict[str, object]:
    """Hits at every k of the ladder, precision@5 and MRR@10."""
    ladder = rt.K_LADDER
    hits = {k: 0 for k in ladder}
    good5 = 0
    rr = Fraction(0)
    for found, relevant in rows:
        for k in ladder:
            if any(name in relevant for name in found[:k]):
                hits[k] += 1
        good5 += sum(1 for name in found[:5] if name in relevant)
        for rank, name in enumerate(found[:max(ladder)], start=1):
            if name in relevant:
                rr += Fraction(1, rank)
                break
    count = len(rows)
    return {"queries": count, "hits": hits,
            "precision_at_5": Fraction(good5, 5 * count) if count else Fraction(0),
            "mrr_at_10": rr / count if count else Fraction(0)}


def _at_least(a: Mapping[str, object], b: Mapping[str, object]) -> bool:
    return (all(a["hits"][k] >= b["hits"][k] for k in rt.K_LADDER)
            and a["mrr_at_10"] >= b["mrr_at_10"])


def _hits_at_least(a: Mapping[str, object], b: Mapping[str, object]) -> bool:
    return all(a["hits"][k] >= b["hits"][k] for k in rt.K_LADDER)


def _lean_set(names: Sequence[str], goal_mode: bool) -> Dict[str, object]:
    """One Lean query set, every ranking, plus the exactness check (W1)."""
    top = max(rt.K_LADDER)
    decls = {d.name: d for d in la.declarations()}
    table = lean_profiles()
    book = lean_book()
    addresses = rt._point_table("address")
    lexical = rt._point_table("lexical")
    corpus = tuple(n for n in rt.corpus() if n in table)
    rows: Dict[str, List] = {scheme: [] for scheme in RANKINGS}
    rows["lexical"] = []
    agree = 0
    for name in names:
        relevant = rt.relatives(name)
        text = rt.strip_declaration_head(decls[name].statement)
        query = Profile(rt.identifier_tokens(text), book)
        if goal_mode:
            point = la.quantise(rt.goal_features(text, exclude=name))
            lex_point = la.quantise(rt.lexical_vector(text))
        else:
            point = addresses.get(name)
            lex_point = lexical.get(name)

        def leech(other: str) -> int:
            there = addresses.get(other)
            if point is None or there is None:
                return 0
            return la.squared_distance(point, there)

        found = {}
        for scheme in RANKINGS:
            found[scheme] = rank_profiles(scheme, query, table, corpus, top,
                                          name, leech)
            rows[scheme].append((tuple(n for n, _ in found[scheme]), relevant))
        if (tuple(v for _, v in found["words_native"])
                == tuple(v for _, v in found["text"])):
            agree += 1
        lex = (rt.rank_by_point(lexical, lex_point, top, name)
               if lex_point is not None else ())
        rows["lexical"].append((tuple(c.name for c in lex), relevant))
    out = {scheme: _tally(r) for scheme, r in rows.items()}
    return {"queries": len(names), "schemes": out,
            "top_values_agree": agree}


@memo
def lean_report() -> Dict[str, object]:
    """W1, W2, W4, W5 and W6 on the two Lean query sets."""
    decl = _lean_set(rt.query_sample(rt.SAMPLE), goal_mode=False)
    goal = _lean_set(rt.query_sample(rt.GOAL_SAMPLE), goal_mode=True)
    book = lean_book()
    return {"declarations": decl, "goals": goal,
            "vocabulary": book.vocabulary_size,
            "injective": book.injective(),
            "declarations_in_corpus": len(lean_profiles())}


@memo
def document_report() -> Dict[str, object]:
    """W1, W3, W4 and W5 on the 60 section queries."""
    ad = _documents()
    state_ = ad.cache_state()
    if not state_["fresh"]:
        return {"answered": False,
                "reason": "the document address book is stale; run "
                          "python3 -m glm_universal.corpus --write"}
    names = ad.query_sample(60)
    k = 5
    rows: Dict[str, List] = {scheme: [] for scheme in RANKINGS}
    rows["lexical"] = []
    rows["text_shipped"] = []
    agree = 0
    relatives = ad.relative_table()
    for name in names:
        relevant = relatives[name]
        text = ad._query_text(name)
        found = {}
        for scheme in RANKINGS:
            found[scheme] = rank_documents(text, k=k, scheme=scheme,
                                           exclude=name)
            rows[scheme].append((tuple(n for n, _ in found[scheme]), relevant))
        if (tuple(v for _, v in found["words_native"])
                == tuple(v for _, v in found["text"])):
            agree += 1
        for scheme, key in (("lexical", "lexical"), ("text_shipped", "text")):
            got = ad.rank(text, k=k, scheme=key, exclude=name)
            rows[scheme].append((tuple(item.name for item in got), relevant))
    scores = {}
    for scheme, r in rows.items():
        count = len(r)
        hits = sum(1 for found, rel in r if any(n in rel for n in found[:k]))
        good = sum(sum(1 for n in found[:k] if n in rel) for found, rel in r)
        scores[scheme] = {"hits": hits,
                          "precision_at_5": Fraction(good, k * count)
                          if count else Fraction(0)}
    book = document_book()
    return {"answered": True, "queries": len(names), "k": k,
            "units": len(ad.units()), "schemes": scores,
            "top_values_agree": agree, "vocabulary": book.vocabulary_size,
            "injective": book.injective()}


@memo
def native_words_report() -> Dict[str, object]:
    """Every declared mark of the study, measured."""
    lean = lean_report()
    docs = document_report()
    decl, goal = lean["declarations"], lean["goals"]
    ds = docs.get("schemes", {})

    def doc_at_least(a: str, b: str) -> bool:
        if not docs.get("answered"):
            return False
        return (ds[a]["hits"] >= ds[b]["hits"]
                and ds[a]["precision_at_5"] >= ds[b]["precision_at_5"])

    def hit5(block: Mapping[str, object], scheme: str) -> int:
        return block["schemes"][scheme]["hits"][5]

    marks = {
        "W1": bool(lean["injective"]) and bool(docs.get("injective"))
              and decl["top_values_agree"] == decl["queries"]
              and goal["top_values_agree"] == goal["queries"]
              and docs.get("top_values_agree") == docs.get("queries"),
        "W2": _at_least(decl["schemes"]["words_native"], decl["schemes"]["text"])
              and _at_least(goal["schemes"]["words_native"],
                            goal["schemes"]["text"]),
        "W3": doc_at_least("words_native", "text"),
        "W4": hit5(decl, "words_native") >= hit5(decl, "text_leech")
              and hit5(goal, "words_native") >= hit5(goal, "text_leech")
              and bool(docs.get("answered"))
              and ds["words_native"]["hits"] >= ds["text_leech"]["hits"],
        "W5": hit5(decl, "letters") > hit5(decl, "lexical")
              and bool(docs.get("answered"))
              and ds["letters"]["hits"] > ds["lexical"]["hits"],
        "W6": _hits_at_least(decl["schemes"]["text_leech"],
                             decl["schemes"]["text"])
              and _hits_at_least(goal["schemes"]["text_leech"],
                                 goal["schemes"]["text"]),
    }
    # Reported beside the marks, never counted among them: comparisons that
    # were not declared before the measurement (the study's §3.3).
    def lean_hits_at_least(a: str, b: str) -> bool:
        return (_hits_at_least(decl["schemes"][a], decl["schemes"][b])
                and _hits_at_least(goal["schemes"][a], goal["schemes"][b]))

    def doc_hits_at_least(a: str, b: str) -> bool:
        return bool(docs.get("answered")) and ds[a]["hits"] >= ds[b]["hits"]

    observed = {
        "letters_vs_text": lean_hits_at_least("letters", "text")
                           and doc_hits_at_least("letters", "text"),
        "letters_vs_parts": lean_hits_at_least("letters", "parts")
                            and doc_hits_at_least("letters", "parts"),
        "words_native_vs_text_parts":
            lean_hits_at_least("words_native", "text_parts")
            and doc_hits_at_least("words_native", "text_parts"),
    }
    return {"lean": lean, "documents": docs, "marks": marks,
            "observed": observed,
            "met": sum(1 for v in marks.values() if v),
            "all_met": all(marks.values()), "study": STUDY,
            "lean_file": LEAN_FILE}


def tool_summary(query: str = "") -> Dict[str, object]:
    """A cheap view: the Golay reading of a text's tokens, for the toolbox."""
    tokens = sorted(rt.identifier_tokens(query))[:12]
    rows = []
    for token in tokens:
        parts = token_parts(token)
        words = [letter_word(p) for p in parts]
        rows.append({"token": token, "parts": parts,
                     "letter_words": [f"{w:06x}" for w in words],
                     "classes": [len(golay_class(w)) for w in words if w]})
    return {"tokens": rows, "study": STUDY}


# ===========================================================================
#  The cache, guarded by a digest
# ===========================================================================

DATA_PATH = Path(__file__).resolve().parent / "_data" / "native_words.json"

_SOURCES: Tuple[str, ...] = (
    "reasoning/native_words.py",
    "reasoning/retrieval.py",
    "reasoning/lean_address.py",
    "substrate/golay_decode.py",
    "corpus/address.py",
    "reasoning/_data/lean_addresses.json",
    "reasoning/_data/lean_lexical_addresses.json",
    "corpus/_data/document_addresses.json",
)


def module_digest() -> str:
    """The digest that decides whether the stored figures are current: the
    **measuring code** only.

    The corpus the figures are taken over -- the Lean tree, the written
    documents and the address books built from them -- is deliberately *not*
    in it.  That corpus includes the study that reports these figures, so
    when it was in the digest, writing the round up made the figures stale,
    re-taking them could move a tie, the study then had to change again, and
    the round could not close on a fixed point.  The figures are a dated
    observation instead: taken over the corpus named by
    :func:`corpus_digest`, re-taken when the code moves or when a session
    decides to (``tools ... --write``), and never by a document edit.
    :func:`corpus_drift` says whether the corpus has moved since.
    """
    root = Path(__file__).resolve().parent.parent
    code = [root / name for name in _SOURCES
            if name.endswith(".py") and (root / name).exists()]
    return integrity.tree_digest(code, root)


def corpus_digest() -> str:
    """The corpus the figures were taken over: books, Lean tree, documents."""
    from ..corpus import inventory as inv
    root = Path(__file__).resolve().parent.parent
    books = integrity.tree_digest([root / name for name in _SOURCES
                                   if not name.endswith(".py")
                                   and (root / name).exists()], root)
    joined = "|".join((books, la.tree_digest(), inv.corpus_digest()))
    return integrity.sha256_hex(joined.encode("utf-8"))


def corpus_drift() -> bool:
    """Whether the corpus has moved since the stored figures were taken.

    Reported, never enforced: a drift is a reason a session *may* re-take the
    figures, not a failure of any gate.
    """
    stored = measurements()
    return stored is None or stored.get("corpus_digest") != corpus_digest()


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
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_thaw(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    payload = dict(native_words_report())
    payload["source_digest"] = module_digest()
    payload["corpus_digest"] = corpus_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    global _cache
    taken = measure()
    documents = taken.get("documents")
    if isinstance(documents, dict) and not documents.get("answered", True):
        # A measurement taken while the document address book was stale
        # would store "not answered" as if it were a result, and every mark
        # read from it would fail.  Refuse, and name the command that fixes it.
        raise RuntimeError(
            "the document address book is stale, so the document marks "
            "cannot be measured; run `python3 -m glm_universal.corpus "
            "--refresh` first")
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(taken), indent=1, sort_keys=True,
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
    _cache = _thaw(loaded) if isinstance(loaded, dict) else None
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
