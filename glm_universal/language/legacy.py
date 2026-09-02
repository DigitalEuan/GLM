"""The three hand-written branches, kept only so the replacement stays measured.

What this module is
-------------------
:mod:`glm_universal.runtime.parser` used to recognise ``derive``, ``measure``
and ``task`` with three hand-written branches: a regular expression per kind,
splitting the remainder of the question on that kind's prepositions.  Those
branches are **gone** from the parser -- the runtime now reads all three off
:mod:`glm_universal.language.descriptions` through the one generic matcher --
and this file is what they said, frozen at the moment they were removed.

Why keep them at all
--------------------
Because the claim the round makes is *the descriptions read these questions
the way the hand-written branches did*, and a claim measured against the code
that replaced them measures nothing.  With the branches deleted,
:func:`glm_universal.language.build.agreement` would be comparing the
descriptions against themselves and would pass no matter what the
descriptions said.  So the branches survive here, called by the measurement
and by nothing else:

* nothing in :mod:`glm_universal.runtime` imports this module -- the test
  ``test_language.py::TestTheBranchesAreGone`` asserts that, so a future
  round cannot quietly route a query back through it;
* it takes the *cleaned* question the parser would have handed the branch and
  returns the same ``(kind, options)`` the branch returned, or ``None`` where
  the branch raised.

The helpers it borrows from the parser -- filler stripping, verb matching,
connective stripping -- are the parser's own and are deliberately *not*
copied: they are shared with every other kind and were never part of what
was deleted.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

__all__ = ["LEGACY_KINDS", "legacy_parse",
           "LEGACY_SHAPED_KINDS", "legacy_parse_shaped"]

#: The kinds this module still knows how to read.  It is exactly the set of
#: branches that were deleted from the parser.
LEGACY_KINDS: Tuple[str, ...] = ("derive", "measure", "task")


def legacy_parse(question: str) -> Optional[Tuple[str, Dict[str, str]]]:
    """``(kind, options)`` as the deleted branch would have produced them.

    ``None`` where the branch raised ``QueryError`` -- which the ``derive``
    branch did when the question named only one thing -- and ``None`` where
    the question is not one of the three kinds at all.
    """
    from ..runtime.parser import (_match_verb, _strip_connectives,
                                  _strip_filler, _strip_verb,
                                  _strip_weak_openers)

    if not question or not question.strip():
        return None
    cleaned = _strip_filler(question)
    lowered = cleaned.lower()
    verb = _match_verb(lowered)
    if verb is None:
        return None
    keyword, kind, _at_start = verb
    if kind not in LEGACY_KINDS:
        return None
    remainder = _strip_weak_openers(_strip_verb(cleaned, keyword))
    options: Dict[str, str] = {}

    if kind == "measure":
        # 'measure hot in tea', 'measure 300 for tea', 'measure hot' -- the
        # split is on the class preposition, and it is made on the raw
        # remainder because ``_strip_connectives`` would eat the ``for``.
        body = remainder.strip(" ?,:")
        subject, comparison = body, ""
        split = re.split(r"\b(?:in|for|against|within)\b|\brelative to\b",
                         body, maxsplit=1, flags=re.IGNORECASE)
        if len(split) == 2:
            subject, comparison = split[0], split[1]
        options["subject"] = _strip_connectives(subject).strip(" ?,:")
        options["class"] = _strip_connectives(comparison).strip(" ?,:")
        return kind, options

    if kind == "derive":
        # 'derive span_ratio of tea', 'derive tet_step of perfect_fifth in
        # harmonics' -- the coordinate and the object are split on 'of', and
        # an optional domain follows 'in'.
        body = _strip_connectives(remainder).strip(" ?,:")
        domain_named = ""
        in_split = re.split(r"\s+in\s+", body, maxsplit=1, flags=re.IGNORECASE)
        if len(in_split) == 2:
            body, domain_named = in_split[0].strip(), in_split[1].strip()
        parts = re.split(r"\s+(?:of|for|on)\s+", body, maxsplit=1,
                         flags=re.IGNORECASE)
        if len(parts) < 2 or not all(part.strip() for part in parts[:2]):
            return None  # the branch raised QueryError here
        options["coordinate"] = parts[0].strip(" ?,:")
        options["object"] = parts[1].strip(" ?,:")
        options["domain"] = domain_named.strip(" ?,:")
        return kind, options

    # 'task <name>' -- the name selects one of the worked end-to-end tasks.
    options["task"] = _strip_connectives(remainder).lower()
    return kind, options


# ===========================================================================
#  THE FOUR SHAPED BRANCHES, FROZEN THE DAY THEY WERE REMOVED
# ===========================================================================
#
#  The round that described the modifier, the list, the trailing option and
#  the nested shape deleted four more branches from the parser: the analogy
#  operator, the comparative between two measured uses, the equation, and
#  both forms of the comparison.  They are here for the same reason the
#  three above are: with the branches gone, an agreement measured against
#  the live parser would be the descriptions measured against themselves.
#
#  The helpers that were part of what was deleted are copied with them --
#  the two comparative regular expressions, the relation table and the
#  semantics keywords.  The helpers that are shared with kinds still coded
#  in the parser (`split_analogy`, `split_equation`, `_top_level_equals`,
#  `_extract_subspace`, `_extract_int_option`, `_split_list`) are imported
#  from it, exactly as before: they were not part of the branch.

#: The comparative form, recognised structurally rather than by keyword
#: (v1.9.0).  ``is hot in tea hotter than cold in stellar_surface`` and
#: ``is warm in tea as hot as cold in stellar_surface`` are the two shapes;
#: the marker is any ``-er than`` word or any ``as <word> as``, and which
#: degree word it is built from -- and therefore which direction it asserts --
#: is decided by the register in
#: :func:`glm_universal.reasoning.measure_view.comparative_stem`, not here.
_COMPARATIVE_INFIX = re.compile(
    r"^\s*(?:is|are|was|were)?\s*(?P<left>.+?)\s+"
    r"(?:(?P<cmp>[a-z][a-z_]*er)\s+than|as\s+(?P<eq>[a-z][a-z_]*)\s+as)\s+"
    r"(?P<right>.+?)\s*$",
    re.IGNORECASE)

#: One side of a comparative: a degree word measured against a class.  The
#: shape is required of *both* sides, which is what keeps the rule from
#: catching ``is sqrt(2) greater than 7/5`` -- an exact-real comparison, whose
#: sides name no comparison class.
_COMPARATIVE_USE = re.compile(
    r"^(?P<word>[A-Za-z][A-Za-z_]*)\s+(?:in|for|against|within)\s+"
    r"(?P<klass>[A-Za-z][A-Za-z_]*)$")


def _split_comparative_use(text: str) -> Optional[Tuple[str, str]]:
    """``hot in tea`` -> ``("hot", "tea")``, or ``None`` if it is not a use."""
    match = _COMPARATIVE_USE.match(text.strip(" ?,:"))
    if match is None:
        return None
    return match.group("word").lower(), match.group("klass").lower()


def _match_comparative(cleaned: str) -> Optional[Dict[str, object]]:
    """Recognise a comparative between two measured uses, or return ``None``.

    Deliberately strict: both sides must be a degree word measured against a
    named class.  A word the register cannot measure still parses -- the
    *refusal* belongs to the measure view, which states the reason -- but an
    expression that is not a use at all does not, so the exact-real
    comparison ``is sqrt(2) greater than 7/5`` is untouched by this rule.
    """
    match = _COMPARATIVE_INFIX.match(cleaned.strip(" ?,:"))
    if match is None:
        return None
    left = _split_comparative_use(match.group("left"))
    right = _split_comparative_use(match.group("right"))
    if left is None or right is None:
        return None
    form = match.group("cmp") or match.group("eq")
    return {
        "form": form.lower(),
        "equative": match.group("eq") is not None,
        "left_word": left[0], "left_class": left[1],
        "right_word": right[0], "right_class": right[1],
    }


#: Comparison keyword -> the relation the question asserts.  ``"compare"``
#: asserts nothing and asks for the order.
_COMPARE_RELATION: Dict[str, str] = {
    "greater than": "greater", "bigger than": "greater",
    "larger than": "greater", "less than": "less",
    "smaller than": "less", "equal to": "equal",
    "the same as": "equal", "compare": "compare",
    "which is bigger": "compare", "which is larger": "compare",
}


#: Words that pin the comparison semantics of a ``verify`` query.  The
#: verifier supports two: ``"scalar"`` compares dimension and decimal scale,
#: ``"full"`` additionally compares tensor rank and P/T/C parity.
SEMANTICS_KEYWORDS: Dict[str, str] = {
    "dimensionally": "scalar", "dimensional": "scalar", "units": "scalar",
    "unit": "scalar", "scalar": "scalar", "magnitude": "scalar",
    "tensor": "full", "full": "full", "rank": "full", "parity": "full",
    "vector": "full",
}


def _detect_semantics(lowered: str) -> Tuple[str, str, Optional[str]]:
    """``(semantics, why, matched_word)`` for a verify query.

    Defaults to ``"scalar"``.  An equation typed without qualification is read
    as a statement about dimensions and decimal scale; asking additionally for
    tensor rank and P/T/C parity is the stricter reading and must be requested
    with a word from :data:`SEMANTICS_KEYWORDS`.  The choice is always
    reported, never silent.

    The matched word is returned so the caller can strip it from the
    expression: a qualifier such as ``"tensor"`` in ``"check tensor force =
    ..."`` is a directive about how to compare, not an operand, and leaving it
    in the expression would make the left side an unknown concept.
    """
    for word in sorted(SEMANTICS_KEYWORDS, key=len, reverse=True):
        if re.search(rf"(?<![a-z0-9_]){re.escape(word)}(?![a-z0-9_])", lowered):
            return (SEMANTICS_KEYWORDS[word],
                    f"keyword {word!r} selected {SEMANTICS_KEYWORDS[word]!r} "
                    f"semantics",
                    word)
    return "scalar", ("no semantics keyword present; defaulted to 'scalar' "
                      "(dimension and decimal scale)"), None


def _strip_semantics_qualifier(body: str, word: Optional[str]) -> str:
    """Remove a semantics qualifier used as a directive, not as an operand.

    Only two positions count as directive use: a leading qualifier
    (``"tensor force = ..."``) and a trailing ``"under <word> semantics"``
    phrase.  A qualifier anywhere else is left alone, because there it is
    plausibly part of an expression and silently deleting it would change the
    equation being audited.
    """
    if not word:
        return body
    out = re.sub(rf"\b(under|in|with)\s+{re.escape(word)}\s+semantics\b\s*$",
                 "", body.strip(), flags=re.IGNORECASE)
    out = re.sub(rf"^\s*{re.escape(word)}(\s+semantics)?(?![a-z0-9_])", "",
                 out, flags=re.IGNORECASE)
    return out.strip(" ,:")


#: The kinds the four frozen shaped branches read.
LEGACY_SHAPED_KINDS: Tuple[str, ...] = (
    "analogy", "comparative", "verify", "compare",
)


def legacy_parse_shaped(question: str
                        ) -> Optional[Tuple[str, Dict[str, object]]]:
    """``(kind, options)`` as the four deleted shaped branches produced them.

    The options are keyed the way the branch keyed them, with the operands
    of the kinds that carried operands under ``"__operands__"`` so that one
    return type serves all four.  ``None`` where the branch raised
    ``QueryError``, and ``None`` where no branch fired.
    """
    from ..runtime.parser import (QueryError, _extract_int_option,
                                  _extract_subspace, _match_verb,
                                  _strip_filler, _strip_verb,
                                  _top_level_equals, split_analogy,
                                  split_equation)

    if not question or not question.strip():
        return None
    cleaned = _strip_filler(question)
    lowered = cleaned.lower()

    # -- the analogy operator ------------------------------------------------
    if "::" in cleaned:
        try:
            a, b, c, _d = split_analogy(cleaned)
        except QueryError:
            return None
        options: Dict[str, object] = {"__operands__": (a, b, c)}
        subspace = _extract_subspace(lowered)
        if subspace:
            options["subspace"] = subspace
        limit = _extract_int_option(lowered, ("top", "limit"))
        if limit is not None:
            options["limit"] = limit
        return "analogy", options

    # -- the comparative between two measured uses ---------------------------
    comparative = _match_comparative(cleaned)
    if comparative is not None:
        return "comparative", dict(comparative)

    verb = _match_verb(lowered)
    equals = _top_level_equals(cleaned)

    if verb is not None and verb[2] and verb[1] != "verify":
        # A leading directive that is not 'verify' took precedence over an
        # '=' later in the line, exactly as it did in the parser.  Of the
        # kinds it could reach only 'compare' was one of the four branches
        # frozen here.
        return _legacy_comparison(cleaned, verb)

    # -- the equation --------------------------------------------------------
    if len(equals) == 1:
        body = cleaned
        if verb is not None and verb[1] == "verify":
            body = _strip_verb(cleaned, verb[0])
        semantics, _why, word = _detect_semantics(lowered)
        stripped = _strip_semantics_qualifier(body, word)
        if stripped != body.strip(" ,:"):
            body = stripped
        try:
            lhs, rhs = split_equation(body)
        except QueryError:
            return None
        return "verify", {"semantics": semantics, "__operands__": (lhs, rhs)}
    if len(equals) > 1:
        return None  # the branch raised QueryError here

    if verb is None:
        return None
    return _legacy_comparison(cleaned, verb)


def _legacy_comparison(cleaned: str, verb: Tuple[str, str, bool]
                       ) -> Optional[Tuple[str, Dict[str, object]]]:
    """The comparison branch, in both of its forms.

    ``None`` for a directive of any other kind -- those kinds were never
    part of the four branches this module freezes -- and ``None`` where the
    branch raised ``QueryError`` for want of a second value.
    """
    from ..runtime.parser import (_split_list, _strip_connectives,
                                  _strip_verb, _strip_weak_openers)

    if verb[1] != "compare":
        return None
    keyword = verb[0]
    remainder = _strip_weak_openers(_strip_verb(cleaned, keyword))
    relation = _COMPARE_RELATION.get(keyword, "compare")
    index_of = cleaned.lower().find(keyword)
    if keyword in ("compare", "which is bigger", "which is larger"):
        body = _strip_connectives(remainder)
        sides = _split_list(body)
        if len(sides) < 2:
            sides = tuple(
                part.strip()
                for part in re.split(r"\bversus\b|\bvs\b|\bor\b|\band\b|,",
                                     body) if part.strip())
    else:
        left = cleaned[:index_of]
        right = cleaned[index_of + len(keyword):]
        left = re.sub(r"^\s*(is|are|does|do)\b", " ", left,
                      flags=re.IGNORECASE)
        sides = (left.strip(" ?,:"), right.strip(" ?,:"))
    if len(sides) < 2 or not all(sides[:2]):
        return None  # the branch raised QueryError here
    return "compare", {"relation": relation, "left": sides[0],
                       "right": sides[1]}
