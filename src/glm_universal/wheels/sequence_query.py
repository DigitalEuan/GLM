"""``glm_universal.wheels.sequence_query`` -- the query surface of the Integer
and Monster Wheels: *what sequence is 1, 1, 2, 3, 5, 8*, *which sporadic
group has order 7920*, *what is the order of the Monster group*.

*Created 31 October 2026 (intake of glm_wheels_bundle; directive D22;
``studies/INTEGER_WHEEL_STUDY.md`` §2).*
*PROVISIONAL (31 October 2026, the owner's decision): installed in the wheels
folder ahead of the Lean build; the item stays in ``source_material/ToDo/``
at Lean written until ``scripts/rebuild_lean.sh`` confirms
``Wheels/IntegerWheel.lean`` and ``Wheels/SporadicOrders.lean``, and answers
that rest on it say so (``glm_universal.wheels.provisional_status``).*
*Last altered 1 November 2026 (Phase 186: intake absorption -- the ``next``
reading added: *what comes next in 1, 1, 2, 5, 14, 42*, answered only when
every entry that starts with the claim and runs past it agrees on the next
term; ``resolve_query(..., next_terms=False)`` is the reading as it was.  The
same day, after the first measurement of*
:mod:`glm_universal.wheels.next_term_battery` *answered its control*
``1, 1, 2, 3, 5`` *with 7: an entry holding the claim from its second stored
term -- the offset-0/1 convention -- that continues differently is a junction
too; ``offset_junctions=False`` is the first rule).*

:func:`answer_sequence_query` returns ``(code, reply)``:

* ``0`` -- answered;
* ``1`` -- a sequence or sporadic-order question that nothing on the wheels
  answers (the reply says so; nothing is guessed);
* ``2`` -- not a sequence or sporadic-order question (the caller should try
  something else).

**Sequence questions** name *sequence* (or ask to *identify* a list) and give
at least three integers (fewer are refused only when the question plainly
asks for a sequence, ``what sequence is 1, 2``).  They are answered by the absorbed Monster Wheel
(the audited Integer Wheel's 107 OEIS entries, ``A000001``, ``A000688``, the
26 sporadic groups and their exponent vectors, and the sorted sporadic
orders): first by ``speak`` (the entry whose stored terms *start with* the
claim; exact matches first, then the least identifier --
``Wheels/IntegerWheel.lean``); when that is silent and the claim has at least
four terms, by ``locate`` (the entry in whose stored terms the claim occurs
earliest after the first term), said as such.

**Next-term questions** are read only in six declared wordings, the whole
question being one of them (:data:`_NEXT_FORM`): *what comes next in a, b, c*,
*what comes next after a, b, c*, *what is the next term of a, b, c*, *what is
the next number in a, b, c*, *next term of a, b, c* and *continue the sequence
a, b, c* (integers only, at least three; *the sequence* may follow the
preposition; a trailing ``?`` is allowed).  The next term is said only when
every entry whose stored terms start with the claim and are longer than it
gives the same next term (the ids are named, least first).  When they
disagree the question is refused as a *junction*, naming each id and its next
term; an entry whose stored terms *equal* the claim is a branch whose
continuation the wheel does not hold, and refuses too.  An entry that holds
the claim from its *second* stored term is the same claim under the other
indexing convention (a sequence listed from index 0 or from index 1, as the
Fibonacci numbers from ``F(0) = 0`` hold ``1, 1, 2, 3, 5`` from their second
term): it is never the source of an answer, but if it continues differently
(or stops at the claim) the question is a junction and is refused.  When no
entry starts with the claim the question is refused, as not on the wheel.
``locate`` (a run inside an entry) is never used for a next term: where such
a run starts is unknown, so what follows it is not determined by the
question.

**Sporadic-order questions** name *sporadic* and give an order -- an integer
or a product of prime powers (``2^4 * 3^2 * 5 * 11``) -- and are answered by
``find_by_order`` (``findByOrder`` in ``Wheels/SporadicOrders.lean``: sound,
and complete over the 26).  The reverse question, *what is the order of the
Monster group*, names a group after *order of*; the reading is narrow (see
:func:`group_named`), so *the order of the B-tree* or *the order of
operations* is left alone (code 2).

The wheel is built once per process and never touches the network.  Integers
only (directive D7).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "ANSWERED", "UNANSWERED", "NOT_MINE", "QueryResult", "resolve_query",
    "answer_sequence_query", "sequence_terms", "parse_order", "group_named",
    "MIN_TERMS", "MIN_LOCATE_TERMS", "next_claim",
]

ANSWERED = 0
UNANSWERED = 1
NOT_MINE = 2

#: A sequence question needs at least this many terms.
MIN_TERMS = 3

#: The run search (``locate``) is tried only on claims at least this long.
MIN_LOCATE_TERMS = 4

#: An order with more digits than this, or a prime power with a larger
#: exponent, is not computed (the Monster's order has 54 digits).
MAX_ORDER_DIGITS = 200
MAX_EXPONENT = 1000


@dataclass(frozen=True)
class QueryResult:
    """What :func:`resolve_query` found: the code, the reply, and the
    identifications in the order the reply names them."""

    code: int
    reply: str
    kind: str = ""                      # "sequence", "next", "order", "reverse" or ""
    ids: Tuple[str, ...] = ()
    order: Optional[int] = None
    position: Optional[int] = None      # where a located run starts
    claim: Tuple[int, ...] = ()
    next_term: Optional[int] = None     # the ``next`` reading's answer
    #: The ``next`` reading's refusal of a junction: ``(id, position, next
    #: term)`` for every entry holding the claim from its first (position 0)
    #: or second (position 1) stored term; the next term is ``None`` for an
    #: entry whose stored terms stop at the claim.
    competing: Tuple[Tuple[str, int, Optional[int]], ...] = ()
    #: The ``next`` reading's answer: the entries holding the claim from their
    #: second stored term, checked and found to agree.
    offset_ids: Tuple[str, ...] = ()


@lru_cache(maxsize=None)
def _default_wheel():
    from .monster_wheel import default_monster_wheel
    return default_monster_wheel()


# ---------------------------------------------------------------------------
# Reading the question
# ---------------------------------------------------------------------------

#: An integer of at most 200 digits (a longer digit string is not a term
#: anyone asks about, and is ignored rather than parsed).
_INT = re.compile(r"(?<![\w.])-?\d{1,200}(?!\w)(?!\.\d)")
_SEQUENCE_CUE = re.compile(r"\b(sequence|sequences|identify)\b", re.I)
_SPORADIC = re.compile(r"\bsporadic\b", re.I)
_ORDER_OF = re.compile(r"\border\s+of\b", re.I)
#: A question that is plainly about a list of terms even with too few of them
#: (``what sequence is 1, 2``); otherwise fewer than :data:`MIN_TERMS`
#: integers (``what sequence of 3 events ...``) is not a sequence question.
_ASKS_FOR_TERMS = re.compile(
    r"\bsequence\s+(?:is|starts|begins|goes)\b|\bidentify\s+the\s+sequence\b",
    re.I)
#: The six wordings of a next-term question, matched against the whole
#: question (white space collapsed, trailing ``?``/``.``/``!`` allowed): the
#: integers in ``terms`` are the claim.
_NEXT_TERMS = r"(?P<terms>-?\d{1,200}(?:\s*,\s*-?\d{1,200})*)"
_NEXT_FORM = re.compile(
    r"(?:(?:what\s+comes\s+next\s+(?:in|after)"
    r"|what\s+is\s+the\s+next\s+term\s+of"
    r"|what\s+is\s+the\s+next\s+number\s+in"
    r"|next\s+term\s+of)(?:\s+the\s+sequence)?"
    r"|continue\s+the\s+sequence)"
    r"\s+" + _NEXT_TERMS + r"\s*[?.!]*",
    re.I)
_ORDER_VALUE = re.compile(
    r"\border(?:\s+(?:of|is|equal\s+to|=))?\s+"
    r"(?P<expr>\d[\d,]*(?:\s*(?:\^|\*\*)\s*\d+)?"
    r"(?:\s*[*·×x]\s*\d+(?:\s*(?:\^|\*\*)\s*\d+)?)*)",
    re.I)

#: Names a question may use for a sporadic group (lower case), longest first
#: where one contains another, with whether the name is distinctive enough to
#: stand alone.  A name that is also an everyday word or a surname (*monster*,
#: *held*, *Thompson*, *Lyons*) is read as the group only when the question
#: says *sporadic* or writes the name before *group* (``the Monster group``):
#: *the order of the monster in the film* is not a group question.
_NAMES: Tuple[Tuple[str, str, bool], ...] = (
    ("baby monster", "B", True),
    ("fischer-griess monster", "M", True),
    ("monster", "M", False),
    ("higman-sims", "HS", True), ("higman sims", "HS", False),
    ("harada-norton", "HN", True), ("harada norton", "HN", False),
    ("mclaughlin", "McL", False),
    ("o'nan", "ON", True), ("onan", "ON", False),
    ("rudvalis", "Ru", True),
    ("held", "He", False),
    ("thompson", "Th", False),
    ("lyons", "Ly", False),
)


def sequence_terms(text: str) -> Tuple[int, ...]:
    """The integers of a question, in order."""
    return tuple(int(m.group(0)) for m in _INT.finditer(text))


def next_claim(text: str) -> Optional[Tuple[int, ...]]:
    """The claim of a next-term question -- the integers of ``text`` when the
    whole of it is one of the six declared wordings (:data:`_NEXT_FORM`) --
    or ``None`` when it is not a next-term question."""
    t = re.sub(r"\s+", " ", (text or "").strip())
    m = _NEXT_FORM.fullmatch(t)
    if not m:
        return None
    return tuple(int(x) for x in re.findall(r"-?\d+", m.group("terms")))


def parse_order(expr: str) -> Optional[int]:
    """An order written as an integer (``7920``, ``7,920``) or a product of
    prime powers (``2^4 * 3^2 * 5 * 11``, ``2**4·3**2``); ``None`` if it is
    neither, or when it is out of all proportion to a group order (more
    than :data:`MAX_ORDER_DIGITS` digits, an exponent above
    :data:`MAX_EXPONENT`): nothing that size is computed."""
    e = expr.strip().rstrip("?.!,")
    if len(e) > 4 * MAX_ORDER_DIGITS:
        return None
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+", e):
        return int(e.replace(",", ""))
    if "," in e:
        return None
    value = 1
    factors = re.split(r"\s*(?:(?<!\*)\*(?!\*)|[·×x])\s*", e)
    for f in factors:
        m = re.fullmatch(r"(\d+)(?:\s*(?:\^|\*\*)\s*(\d+))?", f.strip())
        if not m:
            return None
        if len(m.group(1)) > MAX_ORDER_DIGITS or (
                m.group(2) and len(m.group(2)) > len(str(MAX_EXPONENT))):
            return None
        base = int(m.group(1))
        exponent = int(m.group(2)) if m.group(2) else 1
        if exponent > MAX_EXPONENT or (base > 1 and exponent * (base.bit_length() - 1)
                                       > 4 * MAX_ORDER_DIGITS):
            return None
        value *= base ** exponent
        if len(str(value)) > MAX_ORDER_DIGITS:
            return None
    return value


def _group_ids() -> Dict[str, str]:
    from .cfsg_seed import CFSG_GROUPS
    return {g[0].lower(): g[0] for g in CFSG_GROUPS}


def group_named(phrase: str, sporadic: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """``(group_id, unknown_token)`` for the phrase after *order of*: the
    sporadic group it names, or the id-like token it names that is no
    sporadic group (``M13``), or ``(None, None)``.

    ``sporadic`` says whether the whole question names the word *sporadic*.
    The reading is deliberately narrow, since a wrong group is a confident
    wrong answer: an id with a digit (``M24``, ``J1``, ``Co1``, ``Fi24'``)
    is read as written (exact case, so ``CO2`` is not ``Co2``); a digit-free
    id (``B``, ``M``, ``HS``, ``He``, ...) only when the question says
    *sporadic* (``the order of the B-tree`` is not the Baby Monster's); a
    name as :data:`_NAMES` says; and an unknown id-like token is reported
    only when the question says *sporadic*.
    """
    text = phrase.strip().rstrip("?.!")
    low = text.lower()
    ids = {gid: gid for gid in _group_ids().values()}
    for name, gid, distinctive in _NAMES:
        m = re.search(r"(?<![\w'-])" + re.escape(name) + r"(?![\w'-])", low)
        if not m:
            continue
        if distinctive or sporadic or re.match(
                r"(?:'s)?\s+(?:simple\s+)?group\b", low[m.end():]):
            return gid, None
    tokens = re.findall(r"[A-Za-z]+\d*'?", text)
    unknown = None
    for tok in tokens:
        has_digit = any(c.isdigit() for c in tok)
        if tok in ids and (has_digit or sporadic):
            return ids[tok], None
        if has_digit and tok.rstrip("'") + "'" in ids:
            return ids[tok.rstrip("'") + "'"], None
        if (sporadic and unknown is None
                and re.fullmatch(r"[A-Za-z]{1,3}\d+'?", tok)):
            unknown = tok
    return None, unknown


# ---------------------------------------------------------------------------
# Answering
# ---------------------------------------------------------------------------

def _terms_text(terms: Sequence[int], limit: int = 8) -> str:
    shown = ", ".join(str(t) for t in terms[:limit])
    return shown + (", ..." if len(terms) > limit else "")


def _answer_order(order: int, wheel) -> QueryResult:
    gid = wheel.find_by_order(order)
    if gid is not None and wheel.group(gid) is None:
        gid = None          # a single-term entry that is no sporadic group
    if gid is None:
        return QueryResult(
            UNANSWERED,
            f"No sporadic simple group has order {order}: it is none of the orders "
            f"of the 26 sporadic groups the wheel holds.",
            kind="order", order=order)
    g = wheel.group(gid)
    return QueryResult(
        ANSWERED,
        f"{gid} — {g.name}: the sporadic simple group of order {order} = "
        f"{g.factorization}. (The 26 sporadic orders are distinct, so the answer "
        f"is unique.)",
        kind="order", ids=(gid,), order=order)


def _answer_reverse(phrase: str, wheel, sporadic: bool) -> Optional[QueryResult]:
    gid, unknown = group_named(phrase, sporadic)
    if gid is not None:
        g = wheel.group(gid)
        return QueryResult(
            ANSWERED,
            f"{gid} — {g.name}: order {g.order} = {g.factorization}.",
            kind="reverse", ids=(gid,), order=g.order)
    if unknown is not None:
        return QueryResult(
            UNANSWERED,
            f"There is no sporadic group named {unknown}: the wheel holds the 26 "
            f"sporadic simple groups and {unknown} is not one of them.",
            kind="reverse")
    return None


def _answer_sequence(claim: Tuple[int, ...], wheel) -> QueryResult:
    if len(claim) < MIN_TERMS:
        return QueryResult(
            UNANSWERED,
            f"Give at least {MIN_TERMS} terms of the sequence; "
            f"{len(claim)} is too few to identify it.",
            kind="sequence", claim=claim)
    spoken = wheel.speak(claim)
    if spoken is not None:
        entry = wheel.get(spoken)
        exact, prefix = wheel.tiers(claim)
        tier = exact if exact else prefix
        others = sorted(e.oeis_id for e in tier if e.oeis_id != spoken)
        rest = entry.terms[len(claim):len(claim) + 4]
        reply = (f"{spoken} — {entry.name}: its terms start "
                 f"{_terms_text(entry.terms[:len(claim)])}")
        if rest:
            reply += f", then {_terms_text(rest, 4)}"
        reply += "."
        if others:
            reply += (f" Also starting with these terms: {', '.join(others[:5])}"
                      + (" ..." if len(others) > 5 else "") + ".")
        return QueryResult(ANSWERED, reply, kind="sequence",
                           ids=(spoken,) + tuple(others), position=0, claim=claim)
    if len(claim) >= MIN_LOCATE_TERMS:
        located = wheel.locate(claim)
        if located is not None:
            oid, k = located
            entry = wheel.get(oid)
            rest = entry.terms[k + len(claim):k + len(claim) + 4]
            reply = (f"{oid} — {entry.name}: your terms are its terms from position "
                     f"{k} (counting the first stored term as 0); it starts "
                     f"{_terms_text(entry.terms[:k])}")
            if rest:
                reply += f" and continues {_terms_text(rest, 4)}"
            reply += "."
            return QueryResult(ANSWERED, reply, kind="sequence", ids=(oid,),
                               position=k, claim=claim)
    return QueryResult(
        UNANSWERED,
        f"No sequence on the wheel holds the terms {_terms_text(claim, 12)} "
        f"(its {len(wheel)} entries are audited OEIS sequences and the 26 sporadic "
        f"groups); nothing is guessed.",
        kind="sequence", claim=claim)


def _branches(claim: Tuple[int, ...], wheel, position: int
              ) -> List[Tuple[str, int, Optional[int]]]:
    """``(id, position, next term)`` for every entry whose stored terms hold
    ``claim`` from ``position`` (``None`` when they stop at the claim)."""
    n = len(claim)
    out: List[Tuple[str, int, Optional[int]]] = []
    for e in wheel.entries():
        t = tuple(e.terms)
        if len(t) >= position + n and t[position:position + n] == claim:
            out.append((e.oeis_id, position,
                        t[position + n] if len(t) > position + n else None))
    out.sort(key=lambda b: b[0])
    return out


def _answer_next(claim: Tuple[int, ...], wheel,
                 offset_junctions: bool = True) -> QueryResult:
    """The ``next`` reading: the next term of ``claim`` when every entry that
    starts with it agrees (and, with ``offset_junctions``, every entry that
    holds it from its second stored term agrees too), else a refusal (a
    junction, or not on the wheel).  Never ``locate``."""
    if len(claim) < MIN_TERMS:
        return QueryResult(
            UNANSWERED,
            f"Give at least {MIN_TERMS} terms of the sequence; "
            f"{len(claim)} is too few to say what comes next.",
            kind="next", claim=claim)
    shown = _terms_text(claim, 12)
    prefix = _branches(claim, wheel, 0)
    shifted = _branches(claim, wheel, 1) if offset_junctions else []
    if not prefix:
        held = ""
        if len(shifted) == 1:
            held = f" ({shifted[0][0]} holds them from its second stored term)"
        elif shifted:
            held = (f" ({', '.join(b[0] for b in shifted[:5])}"
                    + (" ..." if len(shifted) > 5 else "")
                    + " hold them from their second stored term)")
        return QueryResult(
            UNANSWERED,
            f"No sequence on the wheel starts with {shown} (its {len(wheel)} "
            f"entries are audited OEIS sequences and the 26 sporadic groups), so "
            f"the wheel cannot say what comes next{held}; a run inside a longer "
            f"sequence is not used, since where it starts is unknown. Nothing "
            f"is guessed.",
            kind="next", claim=claim)
    branches = prefix + shifted
    values = {v for _, _, v in branches}
    ids = tuple(oid for oid, _, _ in prefix)
    if len(values) == 1 and None not in values:
        value = prefix[0][2]
        if len(prefix) == 1:
            entry = wheel.get(ids[0])
            reply = (f"{value} — the next term of {ids[0]} ({entry.name}), the only "
                     f"sequence on the wheel that starts {shown} and runs past it.")
        else:
            reply = (f"{value} — every sequence on the wheel that starts {shown} "
                     f"and runs past it continues with {value}: "
                     + ", ".join(f"{oid} ({wheel.get(oid).name})" for oid in ids)
                     + ".")
        return QueryResult(ANSWERED, reply, kind="next", ids=ids, claim=claim,
                           next_term=value, position=0,
                           offset_ids=tuple(b[0] for b in shifted))
    parts = []
    for oid, pos, v in branches:
        name = wheel.get(oid).name
        where = ", from its second stored term," if pos else ""
        parts.append(f"{oid} ({name}){where} continues with {v}" if v is not None else
                     f"{oid} ({name}){where} stores these terms and no more")
    return QueryResult(
        UNANSWERED,
        f"A junction: the sequences on the wheel that hold {shown} "
        + ("from their first or second stored term" if shifted else
           "from their first stored term")
        + " do not agree on what comes next -- " + "; ".join(parts)
        + ". Nothing is chosen.",
        kind="next", ids=tuple(sorted({b[0] for b in branches})), claim=claim,
        competing=tuple(branches))


def resolve_query(text: str, wheel=None, next_terms: bool = True,
                  offset_junctions: bool = True) -> QueryResult:
    """The full result of :func:`answer_sequence_query` (the identifications
    as well as the reply).  ``wheel`` defaults to the absorbed Monster Wheel;
    the study passes the supplied, unaudited one as its control.

    ``next_terms=False`` leaves the ``next`` reading out: the reading as it was
    before Phase 186 (the baseline of
    :mod:`glm_universal.wheels.next_term_battery`); ``offset_junctions=False``
    gives the ``next`` reading's first rule, without the junctions an entry
    holding the claim from its second stored term makes (kept so that the
    battery's first measurement can be reproduced)."""
    w = wheel if wheel is not None else _default_wheel()
    if not text or not text.strip():
        return QueryResult(NOT_MINE, "")
    # The next-term question: the whole text is one of the six wordings.
    if next_terms:
        claim = next_claim(text)
        if claim is not None:
            return _answer_next(claim, w, offset_junctions)
    sporadic = bool(_SPORADIC.search(text))
    # The forward order question: "... sporadic ... order <n or product>".
    if sporadic:
        m = _ORDER_VALUE.search(text)
        if m:
            order = parse_order(m.group("expr"))
            if order is not None:
                return _answer_order(order, w)
    # The reverse question: "... order of <a sporadic group>".
    m = _ORDER_OF.search(text)
    if m:
        phrase = text[m.end():]
        result = _answer_reverse(phrase, w, sporadic)
        if result is not None:
            return result
        if sporadic:
            return QueryResult(
                UNANSWERED,
                "That names no sporadic group the wheel holds (the 26: M11, M12, "
                "M22, M23, M24, J1-J4, Co1-Co3, HS, McL, He, Ru, Suz, ON, Fi22, Fi23, "
                "Fi24', HN, Th, Ly, B, M).", kind="reverse")
    if sporadic and re.search(r"\border\b", text, re.I):
        return QueryResult(
            UNANSWERED,
            "Ask with the order as an integer or a product of prime powers, e.g. "
            "'which sporadic group has order 7920'.", kind="order")
    # The sequence question.
    if _SEQUENCE_CUE.search(text):
        claim = sequence_terms(text)
        if len(claim) >= MIN_TERMS or (claim and _ASKS_FOR_TERMS.search(text)):
            return _answer_sequence(claim, w)
    return QueryResult(NOT_MINE, "")


def answer_sequence_query(text: str) -> Tuple[int, str]:
    """``(code, reply)`` for a question: ``0`` answered, ``1`` a sequence or
    sporadic-order question nothing answers, ``2`` not such a question.

    >>> answer_sequence_query("which sporadic group has order 7920")[0]
    0
    """
    r = resolve_query(text)
    return r.code, r.reply
