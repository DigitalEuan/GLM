"""``glm_universal.reasoning.golay_words`` -- the Golay words of tokens.

The objects and the Lean-corpus ranking of Phase 71's native word overlap
(``studies/NATIVE_WORDS_STUDY.md``), split out of
:mod:`glm_universal.reasoning.native_words` in Phase 114 so that a caller who
only needs a token's Golay reading -- the toolbox's ``native_words`` tool, and
the ``words_*`` schemes of :mod:`glm_universal.reasoning.retrieval` -- does
not reach the document corpus.  :mod:`~glm_universal.reasoning.native_words`
re-exports every name here and keeps the document half and the measurement.

Everything is an integer, a mask or a :class:`~fractions.Fraction` (D7); no
digest is in any key (D3).  The Lean half is
``RequestProject/GLM/NativeWords.lean``.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import (Callable, Dict, FrozenSet, Iterable, List, Mapping,
                    Optional, Sequence, Tuple)

from ..derived import memo
from ..substrate import golay_decode as gd
from . import lean_address as la
from . import retrieval as rt

__all__ = [
    "letter_word", "token_parts", "golay_class", "NameBook", "Profile",
    "profile", "jaccard", "RANKINGS", "DECLARED", "rank_profiles",
    "lean_book", "lean_profiles", "rank_lean", "tool_summary",
]

STUDY = "studies/NATIVE_WORDS_STUDY.md"

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
