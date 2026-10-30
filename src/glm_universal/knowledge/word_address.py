"""``glm_universal.knowledge.word_address`` -- a word's place on the Leech lattice.

Phase 155, ``studies/CORPUS_DEFINITIONS_STUDY.md`` §2.2.  A word of the corpus
is given 24 integer coordinates -- its association with each of 24 anchor
words chosen by count alone -- and the nearest Leech point to 9 times that
vector is its **address**, by the same decoder and scale the Lean declarations
are addressed with (:func:`glm_universal.reasoning.lean_address.quantise`).
So a word sits on the same lattice as a carrier, a declaration and a document
section, and the read-back is exact (``Address.lean``, ``readback_exact``).

The coordinate of word ``w`` against anchor ``a`` (``CorpusDefinitions.coord``):
``0`` when the four-token-window count ``n(w,a)`` is below 2, otherwise
``6 + ⌊log₂ L⌋`` clamped to ``[1, 12]``, with ``L = n(w,a)·T²/(n(w)·n(a)·P)``
the exact lift as a :class:`~fractions.Fraction`.  A word against itself is 12.

Nothing samples and nothing is a float; the control permutation is the
project's deterministic null model.
"""

from __future__ import annotations

import os
import pickle
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..reasoning import lean_address as la
from . import model as mdl
from . import study as cks

ANCHORS = 24
CAP = 12
CENTRE = 6
NEIGHBOURS = 10
NULL_LABEL = "glm-word-address-null"

Vector = Tuple[int, ...]


def floor_log2(value: Fraction) -> int:
    """``⌊log₂ value⌋`` for a positive fraction, in integers (``Int.log 2``)."""
    if value <= 0:
        raise ValueError("floor_log2 needs a positive value")
    p, q = value.numerator, value.denominator
    k = p.bit_length() - q.bit_length()
    # 2**k <= p/q < 2**(k+1) after at most one correction downwards
    if k >= 0:
        if p < (q << k):
            k -= 1
    elif (p << -k) < q:
        k -= 1
    return k


SCHEMES = ("window", "positional")

#: The positional scheme reads this many anchors, each on the left and the right.
POSITIONAL_ANCHORS = 12


def anchors(model: mdl.Model, scheme: str = "window") -> Tuple[str, ...]:
    """The anchors of a scheme, chosen by count alone.

    ``window``: the 24 alphabetic content words of at least four letters with
    the largest document frequency.  ``positional`` (§2.3): the 12 most
    frequent tokens, function words included.  Ties by spelling.
    """
    if scheme == "positional":
        ranked = sorted(model.unigram, key=lambda w: (-model.unigram[w], w))
        return tuple(ranked[:POSITIONAL_ANCHORS])
    if scheme != "window":
        raise ValueError(f"scheme must be one of {SCHEMES}")
    words = [w for w in model.df if mdl.is_content(w) and len(w) >= 4 and w.isalpha()]
    words.sort(key=lambda w: (-model.df[w], w))
    return tuple(words[:ANCHORS])


def coordinate(model: mdl.Model, word: str, anchor: str) -> int:
    if word == anchor:
        return CAP
    key = (word, anchor) if word < anchor else (anchor, word)
    n = model.window.get(key, 0)
    if n < mdl.MIN_PAIR:
        return 0
    denominator = model.unigram[word] * model.unigram[anchor] * model.window_pairs
    if denominator == 0 or model.tokens == 0:
        return 0
    lift = Fraction(n * model.tokens * model.tokens, denominator)
    return max(1, min(CAP, CENTRE + floor_log2(lift)))


def _bigram_coordinate(model: mdl.Model, first: str, second: str, word: str,
                       anchor: str) -> int:
    """``6 + ⌊log₂(n·T / (n(a)·n(w)))⌋`` clamped, for ``n`` the count of ``first second``."""
    n = model.ctx1.get(first, {}).get(second, 0)
    if n < mdl.MIN_PAIR:
        return 0
    denominator = model.unigram[anchor] * model.unigram[word]
    if denominator == 0 or model.tokens == 0:
        return 0
    return max(1, min(CAP, CENTRE + floor_log2(Fraction(n * model.tokens, denominator))))


def vector(model: mdl.Model, word: str, anchor_words: Sequence[str],
           scheme: str = "window") -> Vector:
    if scheme == "positional":
        left = tuple(_bigram_coordinate(model, a, word, word, a) for a in anchor_words)
        right = tuple(_bigram_coordinate(model, word, a, word, a) for a in anchor_words)
        return left + right
    return tuple(coordinate(model, word, a) for a in anchor_words)


# ---------------------------------------------------------------------------
#  The address book, cached per corpus digest
# ---------------------------------------------------------------------------

_BOOK: Dict[str, Dict[str, object]] = {}


def _cache_path(scheme: str):
    return mdl.CACHE_DIRECTORY / f"word_addresses_{scheme}.pickle"


def address_book(knowledge: Optional[mdl.Knowledge] = None, scheme: str = "window"
                 ) -> Dict[str, object]:
    """Every word's coordinates and address, for the corpus as it now is."""
    knowledge = mdl.load() if knowledge is None else knowledge
    key = f"{scheme}:{knowledge.digest}"
    if key in _BOOK:
        return _BOOK[key]
    path = _cache_path(scheme)
    # Only the corpus as loaded from disk is cached on disk; a corpus built in
    # memory (a test's, a hold-out's) is kept in memory only.
    persistent = mdl._LOADED.get("current") is knowledge
    if persistent and path.exists():
        try:
            with path.open("rb") as handle:
                book = pickle.load(handle)
            if book.get("digest") == knowledge.digest and book.get("scale") == la.SCALE:
                _BOOK[key] = book
                return book
        except Exception:  # pragma: no cover - a corrupt cache is rebuilt
            pass
    model = knowledge.model
    anchor_words = anchors(model, scheme)
    words = tuple(sorted(knowledge.contexts))
    vectors = {w: vector(model, w, anchor_words, scheme) for w in words}
    by_vector: Dict[Vector, Vector] = {}
    for v in sorted(set(vectors.values())):
        by_vector[v] = la.quantise(v)
    book = {"digest": knowledge.digest, "scale": la.SCALE, "scheme": scheme,
            "anchors": anchor_words,
            "words": words, "vectors": vectors,
            "addresses": {w: by_vector[vectors[w]] for w in words}}
    if persistent:
        mdl.CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(f"{path.name}.{os.getpid()}.partial")
        with partial.open("wb") as handle:
            pickle.dump(book, handle, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(partial, path)
    _BOOK[key] = book
    return book


def _index(addresses: Dict[str, Vector], counts) -> Dict[Vector, List[str]]:
    out: Dict[Vector, List[str]] = {}
    for w, a in addresses.items():
        out.setdefault(a, []).append(w)
    for ws in out.values():
        ws.sort(key=lambda w: (-counts[w], w))
    return out


def nearest(word: str, addresses: Dict[str, Vector], index: Dict[Vector, List[str]],
            k: int = NEIGHBOURS) -> List[Tuple[str, int]]:
    """The ``k`` nearest other words: squared distance, then larger count, then spelling."""
    here = addresses[word]
    ranked = sorted((la.squared_distance(here, a), a) for a in index)
    out: List[Tuple[str, int]] = []
    for d, a in ranked:
        for w in index[a]:
            if w != word:
                out.append((w, d))
                if len(out) == k:
                    return out
    return out


def control_addresses(book: Dict[str, object]) -> Dict[str, Vector]:
    words = book["words"]
    perm = integrity.seeded_permutation(len(words), NULL_LABEL)
    addresses = book["addresses"]
    return {w: addresses[words[perm[i]]] for i, w in enumerate(words)}


# ---------------------------------------------------------------------------
#  The reading: a word's address and its neighbours on the lattice
# ---------------------------------------------------------------------------

def locate(word: str, knowledge: Optional[mdl.Knowledge] = None,
           scheme: str = "window") -> Dict[str, object]:
    knowledge = mdl.load() if knowledge is None else knowledge
    book = address_book(knowledge, scheme)
    word = word.strip().lower()
    if word not in book["addresses"]:
        seen = knowledge.model.unigram.get(word, 0)
        return {"ok": False, "word": word, "refusal": (
            f"the corpus never uses {word!r}" if not seen else
            f"{word!r} occurs {seen} times, too little company for a context "
            f"set, so it has no coordinates")}
    index = _index(book["addresses"], knowledge.model.unigram)
    v = book["vectors"][word]
    names = (tuple(f"{a} _" for a in book["anchors"]) + tuple(f"_ {a}" for a in book["anchors"])
             if scheme == "positional" else book["anchors"])
    return {"ok": True, "word": word, "scheme": scheme, "address": book["addresses"][word],
            "coordinates": dict(zip(names, v)),
            "readback": tuple(la.describe_address(book["addresses"][word])["recovered"]) == v,
            "neighbours": nearest(word, book["addresses"], index)}


# ---------------------------------------------------------------------------
#  The marks W1-W4
# ---------------------------------------------------------------------------

def _ratio(a: int, b: int) -> Fraction:
    return Fraction(a, b) if b else Fraction(0)


def compute(knowledge: Optional[mdl.Knowledge] = None, scheme: str = "window"
            ) -> Dict[str, object]:
    knowledge = mdl.load() if knowledge is None else knowledge
    book = address_book(knowledge, scheme)
    counts = knowledge.model.unigram
    words = book["words"]
    addresses = book["addresses"]
    vectors = book["vectors"]
    readback = sum(1 for w in words
                   if tuple(la.describe_address(addresses[w])["recovered"]) == vectors[w])
    distinct_vectors = len(set(vectors.values()))
    distinct_addresses = len(set(addresses.values()))
    control = control_addresses(book)
    index = _index(addresses, counts)
    control_index = _index(control, counts)

    numbers = [w for w in cks.NUMBER_WORDS if w in addresses]
    number_set = set(cks.NUMBER_WORDS)
    num_hits = num_ctrl = 0
    number_rows = []
    for w in numbers:
        near = [x for x, _ in nearest(w, addresses, index)]
        ctrl = [x for x, _ in nearest(w, control, control_index)]
        h = sum(1 for x in near if x in number_set)
        num_hits += h
        num_ctrl += sum(1 for x in ctrl if x in number_set)
        number_rows.append({"word": w, "neighbours": near, "number_words": h})
    num_total = NEIGHBOURS * len(numbers)

    pairs = cks.plural_pairs(knowledge)
    pairs = [(w, p) for w, p in pairs if w in addresses and p in addresses]
    hits = ctrl_hits = 0
    examples = []
    for w, p in pairs:
        h = p in [x for x, _ in nearest(w, addresses, index)]
        hits += h
        ctrl_hits += p in [x for x, _ in nearest(w, control, control_index)]
        if h and len(examples) < 12:
            examples.append({"word": w, "plural": p})
    rate = _ratio(hits, len(pairs))
    ctrl_rate = _ratio(ctrl_hits, len(pairs))
    chance = _ratio(NEIGHBOURS, len(words))
    share = _ratio(num_hits, num_total)
    ctrl_share = _ratio(num_ctrl, num_total)
    marks = {
        "W1": readback == len(words),
        "W2": share >= Fraction(1, 4) and share >= 10 * ctrl_share,
        "W3": rate >= Fraction(1, 10)
              and (rate >= 10 * ctrl_rate if ctrl_hits else rate >= 10 * chance),
        "W4": distinct_vectors == distinct_addresses,
    }
    return {
        "scheme": scheme,
        "words": len(words), "anchors": list(book["anchors"]),
        "scale": book["scale"],
        "readback": readback,
        "distinct_vectors": distinct_vectors,
        "distinct_addresses": distinct_addresses,
        "number_share": share, "number_control_share": ctrl_share,
        "number_rows": number_rows,
        "pairs": len(pairs), "plural_hits": hits, "plural_rate": rate,
        "plural_control_hits": ctrl_hits, "plural_control_rate": ctrl_rate,
        "chance": chance, "plural_examples": examples,
        "marks": marks, "met": sum(1 for v in marks.values() if v),
    }
