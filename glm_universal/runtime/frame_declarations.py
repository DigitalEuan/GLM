"""``glm_universal.runtime.frame_declarations`` -- the stepwise planner's
fold frames as one declaration, and the reader generated from it.

Why this module exists
----------------------
Rounds three and four of the stepwise planner (Phases 84 and 85,
``studies/STEPWISE_THREE_STUDY.md``, ``studies/HOLE_FOLDS_STUDY.md``) read
their folds through hand-written frames: a regular expression and a few
lines of code for each shape of question.  H's E6
(``studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md`` §8) asked for the frames to
be **generated from a declaration** instead, and the roadmap
(``studies/ROADMAP_STUDY.md``) put that first in round 4 of the order of
work so that the widenings after it would be declarations rather than code.
``studies/DECLARED_FRAMES_STUDY.md`` (Phase 91) is the study.

The declaration is three tables:

* :data:`VOCABULARIES` -- each vocabulary a fold slot reads: ``word -> (fold,
  round)``.  The round is the round that declared the word, so the reader can
  be generated for any set of rounds.
* :data:`FRAMES` -- each frame: the round that declared it, the level it is
  read at (an expression span, or a whole ``then``-segment), a template whose
  slots (``{fn}``, ``{column}``, ``{set}``, ``{row}``, ``{count}``,
  ``{sup}``, ``{inner}``) are filled from the vocabularies, the vocabularies
  its ``{fn}`` slot reads with the scope each may be read over (``whole``:
  over the whole set or its present rows; ``present``: over the present rows
  only), and the tree it builds.  Frames are tried in the declared order.
* the round-five declarations the widenings rest on: :data:`SUPERLATIVES`
  (each superlative and the declared comparative it is the superlative of),
  :data:`RANGES` (each declared physical range of a column, with the argument
  for it), and :data:`COUNT_WORDS` and :data:`ORDINALS`.

:func:`read` is the generated reader.  It compiles each frame's template
once per set of rounds, with each slot replaced by its pattern (a fold slot
by the alternation of its vocabularies' words, longest first), and on a
match hands the groups to the builder the frame names.  There are four
builders -- one per kind of tree, not one per frame: ``fold4`` (a fold that
may be read over the present rows), ``fold`` (a fold over the whole set),
``top`` (the row or rows a superlative names) and ``bounds`` (the bounds on
an inner fold).  A builder returns ``None`` when the frame does not apply,
and the next frame is tried; a refusal propagates.

The hand-written readers of rounds three and four stay in
:mod:`glm_universal.runtime.stepwise` as the control the generated reader is
measured against (mark D1); the live path reads through :func:`read`.

Exact throughout; nothing here reads a digest or a similarity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple

__all__ = ["Frame", "VOCABULARIES", "FRAMES", "SUPERLATIVES", "RANGES",
           "COUNT_WORDS", "ORDINALS", "GENERATED", "read", "frames_for",
           "vocabulary", "is_order_fold", "declared_range", "superlative",
           "ROUND_FIVE_WORDS", "declaration_census", "emptied",
           "ROUND_FIVE", "DECLARE_ROUND_FIVE", "five",
           "declared_verdict"]

#: Whether the live path reads folds through the generated reader (on) or
#: through the hand-written readers of rounds three and four (off).  Off
#: only in the census of mark D1.
GENERATED = True

#: Round five (Phase 91): the round's own switch.  Off, the planner is
#: round four's reader -- the control of marks D2-D5.
ROUND_FIVE = True

#: Whether the round-five **entries** of every declaration are present
#: (frames, words, sets, prefixes, molecule comparatives, ranges).  Off with
#: :data:`ROUND_FIVE` still on is mark D5's control: every widening must
#: hang on an entry, so removing the entries alone must give round four's
#: verdicts back.
DECLARE_ROUND_FIVE = True


def five() -> bool:
    """Whether round five's entries are read."""
    return ROUND_FIVE and DECLARE_ROUND_FIVE

# ---------------------------------------------------------------------------
# the vocabularies
# ---------------------------------------------------------------------------

#: Ordinal words read in front of *largest* / *smallest* (round five).
ORDINALS: Dict[str, int] = {
    "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    "2nd": 2, "3rd": 3, "4th": 4, "5th": 5, "6th": 6, "7th": 7, "8th": 8,
    "9th": 9, "10th": 10,
}

#: Count words read in front of a superlative (round five): *the three
#: heaviest*.
COUNT_WORDS: Dict[str, int] = {
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "twenty": 20,
}

_LARGEST = ("largest", "highest", "greatest")
_SMALLEST = ("smallest", "lowest")


def _ordinal_words() -> Dict[str, Tuple[str, int]]:
    out: Dict[str, Tuple[str, int]] = {}
    for word, k in ORDINALS.items():
        for big in _LARGEST:
            out[f"{word} {big}"] = (f"max:{k}", 5)
        for small in _SMALLEST:
            out[f"{word} {small}"] = (f"min:{k}", 5)
    return out


#: ``vocabulary -> {word -> (fold, round that declared it)}``.
VOCABULARIES: Dict[str, Dict[str, Tuple[str, int]]] = {
    # round three (Phase 84): the free folds
    "fold": {"sum": ("sum", 3), "total": ("sum", 3), "average": ("mean", 3),
             "mean": ("mean", 3), "arithmetic mean": ("mean", 3)},
    # round four (Phase 85): the order folds; round five adds the quartiles
    # and the k-th largest and smallest
    "order": dict({"median": ("median", 4), "largest": ("max", 4),
                   "highest": ("max", 4), "maximum": ("max", 4),
                   "greatest": ("max", 4), "smallest": ("min", 4),
                   "lowest": ("min", 4), "minimum": ("min", 4),
                   "lower quartile": ("q1", 5), "first quartile": ("q1", 5),
                   "upper quartile": ("q3", 5), "third quartile": ("q3", 5)},
                  **_ordinal_words()),
    # round three: the parity counts
    "parity": {"odd": ("odd", 3), "even": ("even", 3)},
}

#: ``superlative -> declared comparative`` (round five): the superlative
#: names the row first by the comparative's column and direction
#: (:data:`glm_universal.runtime.declared_frames.COMPARATIVES`).
SUPERLATIVES: Dict[str, str] = {
    "heaviest": "heavier", "lightest": "lighter", "densest": "denser",
    "oldest": "older", "newest": "newer",
}

#: ``element-table column -> (L, U, the argument)``: the declared physical
#: range a missing reading of the column must lie in (round five).  Only a
#: two-sided range bounds a sum or a mean; a column not listed is refused
#: ``RANGE_UNDECLARED`` when its bounds are asked for under a hole.
RANGES: Dict[str, Tuple[Fraction, Fraction, str]] = {
    "electronegativity_pauling": (
        Fraction(0), Fraction(398, 100),
        "the Pauling scale is positive, and fluorine's 3.98 is the largest "
        "value on it"),
    "ionization_energy_eV": (
        Fraction(0), Fraction(24587, 1000),
        "a first ionization energy is positive, and helium's 24.587 eV is "
        "the largest of any element"),
}


def vocabulary(name: str, rounds: FrozenSet[int]) -> Dict[str, str]:
    """``word -> fold`` of one vocabulary, restricted to ``rounds``."""
    return {w: fn for w, (fn, r) in VOCABULARIES[name].items()
            if r in rounds}


def is_order_fold(fn: str) -> bool:
    """Whether ``fn`` is an order fold (bounded rather than freed by a
    hole): round four's median, ends and rank, and round five's quartiles
    and k-th values."""
    return fn in ("median", "max", "min", "rank", "q1", "q3") or \
        bool(re.fullmatch(r"(?:max|min):\d+", fn))


def declared_range(field: str) -> Optional[Tuple[Fraction, Fraction]]:
    """The declared range of a column, or None."""
    got = RANGES.get(field)
    return (got[0], got[1]) if got else None


def superlative(word: str) -> Optional[Tuple[str, str, str]]:
    """``(comparative, register phrase, direction)`` of a declared
    superlative, or None."""
    from .declared_frames import COMPARATIVES
    comp = SUPERLATIVES.get(word)
    if comp is None:
        return None
    phrase, sym, _gloss = COMPARATIVES[comp]
    return comp, phrase, sym


#: The words round five adds, by vocabulary -- the entries D5's control
#: removes.
ROUND_FIVE_WORDS: Dict[str, Tuple[str, ...]] = {
    name: tuple(w for w, (_fn, r) in voc.items() if r == 5)
    for name, voc in VOCABULARIES.items()}

# ---------------------------------------------------------------------------
# the frames
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Frame:
    """One declared frame.

    ``vocab`` pairs each vocabulary the ``{fn}`` slot reads with the scope
    its words may be read over: ``whole`` (the whole set, or its present
    rows when the set phrase asks for them) or ``present`` (only the present
    rows).  ``build`` names the builder: ``fold4``, ``fold``, ``top`` or
    ``bounds``.  ``fixed`` is the fold of a frame with no ``{fn}`` slot.
    """

    name: str
    round: int
    level: str                       # "expression" or "segment"
    template: str
    build: str
    vocab: Tuple[Tuple[str, str], ...] = ()
    fixed: Optional[str] = None
    gloss: str = ""


#: The declaration, in the order the frames are tried.  Round four's frames
#: come before round three's, as the hand-written readers ran them.
FRAMES: Tuple[Frame, ...] = (
    Frame("rank", 4, "expression", "rank of {row} by {column} among {set}",
          "fold4", fixed="rank",
          gloss="the rank of a row by a column within a declared set"),
    Frame("order-of", 4, "expression", "{fn} of (?:the )?{column} of {set}",
          "fold4", vocab=(("order", "whole"), ("fold", "present")),
          gloss="an order fold, or a free fold over the present rows: "
                "the median of the Xs of S"),
    Frame("order-x", 4, "expression", "{fn} (?!of ){column} of {set}",
          "fold4", vocab=(("order", "whole"), ("fold", "present")),
          gloss="the same, written the median X of S"),
    Frame("fold-of", 3, "expression", "{fn} of (?:the )?{column} of {set}",
          "fold", vocab=(("fold", "whole"),),
          gloss="a free fold over the whole set: the sum of the Xs of S"),
    Frame("fold-x", 3, "expression", "{fn} (?!of ){column} of {set}",
          "fold", vocab=(("fold", "whole"),),
          gloss="the same, written the average X of S"),
    Frame("bounds", 5, "segment", "(?:what are )?the bounds on {inner}",
          "bounds", gloss="the bounds on a free fold or a parity count"),
    Frame("superlative-one", 5, "segment", "which is the {sup} of {set}",
          "top", gloss="the row a superlative names"),
    Frame("superlative-k", 5, "segment",
          "(?:what|which) are the {count} {sup} {set}", "top",
          gloss="the k rows a superlative names, first to last"),
    Frame("parity-present", 5, "segment",
          "how many of {set} (?:have|has) an? {fn} {column}", "fold4",
          vocab=(("parity", "present"),),
          gloss="a parity count over the present rows"),
    Frame("parity", 3, "segment",
          "how many of {set} (?:have|has) an? {fn} {column}", "fold",
          vocab=(("parity", "whole"),),
          gloss="a parity count over the whole set"),
)

_SLOTS = {"column": r"(?P<column>.+?)", "set": r"(?P<set>.+)",
          "row": r"(?P<row>.+?)", "inner": r"(?P<inner>.+)",
          "sup": r"(?P<sup>\w+est)"}


def _alternation(words) -> str:
    return "|".join(sorted(map(re.escape, words), key=len, reverse=True))


def frames_for(rounds: FrozenSet[int], level: str) -> List[Frame]:
    """The declared frames of ``rounds`` at one level, in order."""
    return [f for f in FRAMES if f.round in rounds and f.level == level]


_COMPILED: Dict[Tuple[str, FrozenSet[int], Tuple], object] = {}


def _words_of(frame: Frame, rounds: FrozenSet[int]) -> Dict[str, Tuple[str,
                                                                       str]]:
    """``word -> (fold, scope)`` the frame's ``{fn}`` slot reads."""
    out: Dict[str, Tuple[str, str]] = {}
    for name, scope in frame.vocab:
        for w, fn in vocabulary(name, rounds).items():
            out.setdefault(w, (fn, scope))
    return out


def _pattern(frame: Frame, rounds: FrozenSet[int]):
    key = (frame.name, rounds, _EMPTIED_KEY[0])
    got = _COMPILED.get(key)
    if got is not None:
        return got
    words = _words_of(frame, rounds)
    slots = dict(_SLOTS)
    slots["fn"] = rf"(?P<fn>{_alternation(words)})" if words else r"(?!)"
    slots["count"] = (rf"(?P<count>{_alternation(COUNT_WORDS)}|\d+)")
    text = frame.template
    last = max(re.finditer(r"\{(\w+)\}", text), key=lambda x: x.start())
    for name, pat in slots.items():
        if name in ("column", "set", "row", "inner"):
            # the last slot of a template is greedy, every other one lazy,
            # as the hand-written frames wrote them
            pat = pat.replace(".+?)", ".+)") if name == last.group(1) \
                else pat.replace(".+)", ".+?)")
        text = text.replace("{" + name + "}", pat)
    got = (re.compile(text), words)
    _COMPILED[key] = got
    return got


# ---------------------------------------------------------------------------
# the builders
# ---------------------------------------------------------------------------

def _build_fold4(frame: Frame, m, words, rounds) -> Optional[List[tuple]]:
    from .stepwise import _fold_set, _present_split
    column = m.group("column")
    if frame.fixed == "rank":
        base, present = _present_split(m.group("set"), column)
        key = _fold_set(base, column)
        if key is None:
            return None
        return [("fold4", "rank", key, column, present,
                 m.group("row").strip())]
    fn, scope = words[m.group("fn")]
    base, present = _present_split(m.group("set"), column)
    if scope == "present" and not present:
        return None
    key = _fold_set(base, column)
    if key is None:
        return None
    return [("fold4", fn, key, column, present, None)]


def _build_fold(frame: Frame, m, words, rounds) -> Optional[List[tuple]]:
    from .stepwise import _fold_set
    fn, _scope = words[m.group("fn")]
    key = _fold_set(m.group("set"), m.group("column"))
    if key is None:
        return None
    return [("fold", fn, key, m.group("column"))]


def _build_top(frame: Frame, m, words, rounds) -> Optional[List[tuple]]:
    from .declared_frames import set_key
    from .stepwise import Refused, _fold_set, _present_split
    word = m.group("sup")
    k = 1
    if "count" in m.groupdict() and m.group("count") is not None:
        c = m.group("count")
        k = int(c) if c.isdigit() else COUNT_WORDS[c]
    got = superlative(word)
    if got is None:
        stripped = re.sub(r"\s+(?:that (?:have|has) .+|with .+)$", "",
                          m.group("set"))
        if set_key(stripped)[0] is not None:
            from .declared_frames import COMPARATIVES
            raise Refused("COMPARATIVE_UNDECLARED",
                          f"{word!r} is no declared superlative: no register "
                          f"column is declared to measure it (the declared "
                          f"ones are {', '.join(sorted(SUPERLATIVES))}, of "
                          f"{', '.join(sorted(COMPARATIVES))})")
        return None
    _comp, phrase, _sym = got
    base, present = _present_split(m.group("set"), phrase)
    key = _fold_set(base, phrase)
    if key is None:
        return None
    return [("top", word, k, key, present)]


def _build_bounds(frame: Frame, m, words, rounds) -> Optional[List[tuple]]:
    inner = m.group("inner").strip()
    from .stepwise import _strip_the
    tree = None
    for f in frames_for(rounds, "expression") + frames_for(rounds, "segment"):
        if f.build != "fold":
            continue
        span = _strip_the(inner) if f.level == "expression" else inner
        pat, w = _pattern(f, rounds)
        mm = pat.fullmatch(span)
        if not mm:
            continue
        got = _build_fold(f, mm, w, rounds)
        if got:
            tree = got[0]
            break
    if tree is None:
        return None
    _, fn, key, column = tree
    return [("bounds", fn, key, column)]


_BUILDERS: Dict[str, Callable] = {"fold4": _build_fold4, "fold": _build_fold,
                                  "top": _build_top, "bounds": _build_bounds}


def read(text: str, rounds: FrozenSet[int], level: str
         ) -> Optional[List[tuple]]:
    """The generated reader: the first declared frame of ``rounds`` at
    ``level`` whose template matches ``text`` and whose builder applies, or
    None.  A refusal raised by a builder propagates."""
    if not five():
        rounds = frozenset(r for r in rounds if r != 5)
    for frame in frames_for(rounds, level):
        if frame.name in _EMPTIED:
            continue
        pat, words = _pattern(frame, rounds)
        m = pat.fullmatch(text)
        if not m:
            continue
        got = _BUILDERS[frame.build](frame, m, words, rounds)
        if got is not None:
            return got
    return None


# ---------------------------------------------------------------------------
# the controls
# ---------------------------------------------------------------------------

_EMPTIED: set = set()
_EMPTIED_KEY = [0]


class emptied:
    """The declaration with every frame removed (D1's control): used as
    ``with emptied(): ...``."""

    def __enter__(self):
        self._saved = set(_EMPTIED)
        _EMPTIED.update(f.name for f in FRAMES)
        _EMPTIED_KEY[0] += 1
        return self

    def __exit__(self, *exc) -> bool:
        _EMPTIED.clear()
        _EMPTIED.update(self._saved)
        _EMPTIED_KEY[0] += 1
        return False


def declared_verdict(corpus: str, cid: str, want):
    """The verdict an earlier round's case is declared to get now: its own,
    or -- for the three cases Phase 91 declared it moves
    (:data:`glm_universal.evaluation.stepwise_five_cases.MOVED`) -- the
    moved verdict while round five's entries are read."""
    from ..evaluation.stepwise_five_cases import MOVED
    got = MOVED.get((corpus, cid))
    if got is None or not five():
        return tuple(want)
    return tuple(got[2])


def declaration_census() -> Dict[str, object]:
    """What the declaration holds: frames and words by round."""
    by_round: Dict[int, int] = {}
    for f in FRAMES:
        by_round[f.round] = by_round.get(f.round, 0) + 1
    words: Dict[int, int] = {}
    for voc in VOCABULARIES.values():
        for _w, (_fn, r) in voc.items():
            words[r] = words.get(r, 0) + 1
    return {"frames": len(FRAMES), "frames_by_round": by_round,
            "words_by_round": words, "superlatives": len(SUPERLATIVES),
            "ranges": len(RANGES), "ordinals": len(ORDINALS),
            "count_words": len(COUNT_WORDS)}
