"""``glm_universal.runtime.tool_values`` -- a tool's answer handed on as a value.

Why this module exists
----------------------
Phase 136 left this line in ``STATUS.md`` §2.2: *a tool's answer is not yet
handed to the planner as a value, so a question that composes a tool with
arithmetic ("twice the third term of the continued fraction of pi") is
refused.*  The stepwise planner already reads *twice …*, *… plus …*, *the gcd
of … and …*, *is … prime?* and *then …*; what it lacked was a leaf: every part
that is not a number is asked of the typed planner, and the typed planner
holds no continued fraction.

This module is that leaf (``studies/TOOL_VALUES_STUDY.md``, Phase 137).  It
reads a **noun phrase naming one number a tool computes** -- *the third term
of the continued fraction of pi*, *the fourth convergent of pi*, *the closest
fraction to sqrt(2) with denominator at most 100*, *the number of gate moves
from 0x7 to 0x3*, *the kissing number of the Leech lattice* -- and returns the
``tool …`` text that computes it with a **selector** that picks the number out
of the tool's figures.  The stepwise planner consults it only for a part the
typed planner refused, so no answer it gave before changes; the step it adds
is an ordinary ``planned`` step, admitted through the same step gate, and the
chain's column-3 script re-runs the tool in a fresh interpreter and applies
the selector itself.

The selectors are few and total over the figures they name:

* ``("index", key, i)`` -- the ``i``-th entry (from 0) of a list figure;
* ``("fold", key, fn, n)`` -- ``sum``, ``product``, ``max``, ``min`` or
  ``mean`` of the first ``n`` entries;
* ``("value", key)`` -- a figure that is itself a number or a fraction;
* ``("part", key, "numerator" | "denominator")`` -- of a fraction figure;
* ``("entry", key, k)`` -- a mapping figure's entry ``k``.

Selecting the ``k``-th term from a certified prefix of length ``k`` is the
``k``-th term of the value (``GLM.ToolValues.cfPrefix_take``,
``GLM.ToolValues.cfPrefix_getElem``), so composition does not weaken what the
tool certified.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = ["ToolValue", "read_value", "select", "evaluate", "ORDINALS",
           "PATTERNS", "answer_text", "ToolVerdict", "read_verdict", "decide",
           "verdict_of_figures"]

ORDINALS: Mapping[str, int] = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
    "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18,
    "nineteenth": 19, "twentieth": 20,
}

_COUNTS: Mapping[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "fifteen": 15, "twenty": 20,
}

_ORD = (r"(" + "|".join(sorted(ORDINALS, key=len, reverse=True))
        + r"|\d+(?:st|nd|rd|th))")
_COUNT = r"(\d+|" + "|".join(sorted(_COUNTS, key=len, reverse=True)) + r")"
_CF = r"(?:simple )?continued[- ]fraction(?: expansion)?"
_TERM = r"(?:term|partial quotient|coefficient|entry)"
_FOLD = {"sum": "sum", "total": "sum", "product": "product",
         "largest": "max", "biggest": "max", "greatest": "max",
         "maximum": "max", "smallest": "min", "least": "min",
         "minimum": "min", "mean": "mean", "average": "mean"}
_FOLDS = "(" + "|".join(sorted(_FOLD, key=len, reverse=True)) + ")"
_BOUND = (r"(at most|up to|no more than|not exceeding|not more than|<=|"
          r"no greater than|of at most|below|less than|under|smaller than|<)")


def _ordinal(word: str) -> int:
    w = word.lower()
    if w in ORDINALS:
        return ORDINALS[w]
    return int(re.match(r"\d+", w).group(0))


def _count(word: str) -> int:
    w = word.lower()
    return _COUNTS[w] if w in _COUNTS else int(w)


@dataclass(frozen=True)
class ToolValue:
    """One number a tool computes: the tool text, and how to pick it out."""

    phrase: str
    tool_text: str
    selector: Tuple[object, ...]
    pattern: str

    @property
    def tool_name(self) -> str:
        from . import toolbox as tb
        rest = self.tool_text[len("tool "):].lower()
        for t in sorted(tb.TOOLS, key=lambda x: -len(x.name)):
            if rest == t.name or rest.startswith(t.name + " "):
                return t.name
        return rest.split(" ")[0]

    def as_list(self) -> List[object]:
        return ["tool", self.tool_text] + [str(s) for s in self.selector]


def _strip(phrase: str) -> str:
    t = phrase.strip().rstrip("?.! ").strip()
    t = re.sub(r"^(?:what is|what's|whats|compute|calculate|find|give me|"
               r"tell me|evaluate)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^the\s+", "", t, flags=re.IGNORECASE)
    return t.strip()


def _cf_term(m) -> Tuple[str, Tuple[object, ...]]:
    k, x = _ordinal(m.group(1)), m.group(2)
    return f"tool continued fraction {x} terms {k}", ("index", "terms", k - 1)


def _cf_term_number(m) -> Tuple[str, Tuple[object, ...]]:
    k, x = int(m.group(1)), m.group(2)
    return f"tool continued fraction {x} terms {k}", ("index", "terms", k - 1)


def _cf_fold(m) -> Tuple[str, Tuple[object, ...]]:
    fn, n, x = _FOLD[m.group(1).lower()], _count(m.group(2)), m.group(3)
    return f"tool continued fraction {x} terms {n}", ("fold", "terms", fn, n)


def _convergent(m) -> Tuple[str, Tuple[object, ...]]:
    part, k, x = m.group(1), _ordinal(m.group(2)), m.group(3)
    sel: Tuple[object, ...] = ("part", "value", part.lower()) if part \
        else ("value", "value")
    return f"tool convergent {k} of {x}", sel


def _convergent_number(m) -> Tuple[str, Tuple[object, ...]]:
    part, k, x = m.group(1), int(m.group(2)), m.group(3)
    sel: Tuple[object, ...] = ("part", "value", part.lower()) if part \
        else ("value", "value")
    return f"tool convergent {k} of {x}", sel


def _approximation(m) -> Tuple[str, Tuple[object, ...]]:
    part, x, how, n = m.group(1), m.group(2), m.group(3).lower(), int(
        m.group(4))
    if how in ("below", "less than", "under", "smaller than", "<"):
        n -= 1
    sel: Tuple[object, ...] = ("part", "value", part.lower()) if part \
        else ("value", "value")
    return f"tool best approximation {x} denominator {n}", sel


def _gates(m) -> Tuple[str, Tuple[object, ...]]:
    return f"tool gates {m.group(1)} to {m.group(2)}", ("value", "moves")


def _kissing(m) -> Tuple[str, Tuple[object, ...]]:
    return "tool llvq", ("value", "kissing_number")


def _leech_shell(m) -> Tuple[str, Tuple[object, ...]]:
    return "tool llvq", ("entry", "shell_counts", str(4 * int(m.group(1))))


def _moonshine(m) -> Tuple[str, Tuple[object, ...]]:
    return "tool moonshine", ("index", "graded_dimensions", int(m.group(1)))


#: ``(name, pattern, builder)``: a full-match pattern over the phrase with its
#: lead (*what is*, *the*) stripped, and the builder of its tool text and
#: selector.  ``X`` is any text the tool itself then reads or refuses.
PATTERNS: Tuple[Tuple[str, str, object], ...] = (
    ("cf-term", _ORD + r" " + _TERM + r" (?:of|in|for) (?:the )?(?:" + _CF
     + r"|expansion) (?:of|for) (.+)", _cf_term),
    # Phase 138: "partial quotient" names a continued-fraction term by
    # itself, so the expansion need not be named (Phase 137's held-out miss
    # "the second partial quotient of pi").
    ("cf-quotient", _ORD + r" partial quotient (?:of|in|for) (?:the )?(?:(?:"
     + _CF + r"|expansion) (?:of|for) )?(.+)", _cf_term),
    ("cf-term-number", _TERM + r" (?:number )?(\d+) (?:of|in|for) (?:the )?(?:"
     + _CF + r"|expansion) (?:of|for) (.+)", _cf_term_number),
    ("cf-quotient-number", r"partial quotient (?:number )?(\d+) (?:of|in|for) "
     r"(?:the )?(?:(?:" + _CF + r"|expansion) (?:of|for) )?(.+)",
     _cf_term_number),
    ("cf-fold", _FOLDS + r" (?:of )?(?:the )?first " + _COUNT + r" (?:terms|"
     r"partial quotients|coefficients|entries) (?:of|in|for) (?:the )?(?:"
     + _CF + r"|expansion) (?:of|for) (.+)", _cf_fold),
    ("cf-quotient-fold", _FOLDS + r" (?:of )?(?:the )?first " + _COUNT
     + r" partial quotients (?:of|in|for) (?:the )?(?:(?:" + _CF
     + r"|expansion) (?:of|for) )?(.+)", _cf_fold),
    # Phase 138: "convergent number 4 of pi", "convergent 4 of pi" (Phase
    # 137's held-out miss).
    ("convergent-number", r"(?:(numerator|denominator) of (?:the )?)?"
     r"convergent (?:number )?(\d+) (?:of|to|for) (?:the )?(?:" + _CF
     + r" (?:of|for) )?(.+)", _convergent_number),
    ("convergent", r"(?:(numerator|denominator) of (?:the )?)?" + _ORD
     + r" convergent (?:of|to|for) (?:the )?(?:" + _CF + r" (?:of|for) )?(.+)",
     _convergent),
    ("approximation", r"(?:(numerator|denominator) of (?:the )?)?(?:best |"
     r"closest |nearest )(?:rational )?(?:approximation|fraction) (?:to|of|"
     r"for) (.+?),? with (?:a )?denominator " + _BOUND + r" (\d+)",
     _approximation),
    ("gates", r"(?:least |smallest |minimum |fewest )?number of (?:reversible "
     r")?(?:toffoli/fredkin |gate |toffoli |fredkin )?(?:gate )?moves "
     r"(?:needed |required )?(?:from|between) (\S+) (?:to|and) (\S+)", _gates),
    ("kissing", r"kissing number of the leech lattice", _kissing),
    ("leech-shell", r"number of (?:vectors|points) of norm (\d+) in the "
     r"leech lattice", _leech_shell),
    ("leech-shell", r"number of leech(?: lattice)? (?:vectors|points) of "
     r"norm (\d+)", _leech_shell),
    ("moonshine", r"dimension of v_?(\d+)(?: of the moonshine module)?",
     _moonshine),
)


def read_value(phrase: str) -> Optional[ToolValue]:
    """The tool value ``phrase`` names, or ``None`` if no pattern reads it."""
    t = _strip(phrase)
    for name, pattern, build in PATTERNS:
        m = re.fullmatch(pattern, t, re.IGNORECASE)
        if m:
            text, sel = build(m)
            return ToolValue(phrase, text, tuple(sel), name)
    return None


def _num(v: object) -> Fraction:
    if isinstance(v, bool):
        raise ValueError(f"{v!r} is a verdict, not a number")
    if isinstance(v, (int, Fraction)):
        return Fraction(v)
    if isinstance(v, str):
        return Fraction(v)
    raise ValueError(f"{v!r} is not a number")


def select(figures: Mapping[str, object], selector: Sequence[object]
           ) -> Fraction:
    """Apply a selector to a tool's figures; raises ``ValueError`` when the
    figure is absent or the selection is out of range."""
    kind, key = selector[0], selector[1]
    if key not in figures:
        raise ValueError(f"the tool gave no figure {key!r}")
    fig = figures[key]
    if kind == "index":
        i = int(selector[2])
        if not isinstance(fig, (list, tuple)) or not 0 <= i < len(fig):
            raise ValueError(f"the tool's {key} has no entry {i + 1}")
        return _num(fig[i])
    if kind == "fold":
        fn, n = selector[2], int(selector[3])
        if not isinstance(fig, (list, tuple)) or len(fig) < n or n < 1:
            raise ValueError(f"the tool's {key} has fewer than {n} entries")
        vals = [_num(v) for v in fig[:n]]
        if fn == "sum":
            return sum(vals, Fraction(0))
        if fn == "product":
            out = Fraction(1)
            for v in vals:
                out *= v
            return out
        if fn == "max":
            return max(vals)
        if fn == "min":
            return min(vals)
        if fn == "mean":
            return sum(vals, Fraction(0)) / n
        raise ValueError(f"no fold {fn!r}")
    if kind == "value":
        return _num(fig)
    if kind == "part":
        q = _num(fig)
        return Fraction(q.numerator if selector[2] == "numerator"
                        else q.denominator)
    if kind == "entry":
        k = str(selector[2])
        if not isinstance(fig, Mapping) or k not in fig:
            raise ValueError(f"the tool's {key} has no entry {k}")
        return _num(fig[k])
    raise ValueError(f"no selector {kind!r}")


def evaluate(tv: ToolValue):
    """``(value, tool_result)`` for a tool value; raises ``ValueError`` with
    the tool's refusal or the selector's when there is no number."""
    from . import toolbox as tb
    got = tb.run_tool(tv.tool_text)
    if not got.ok:
        raise ValueError(got.text)
    return select(got.figures, tv.selector), got


def _render(v: Fraction) -> str:
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/" \
        f"{v.denominator}"


def answer_text(phrase: str) -> Optional[Tuple[str, ToolValue, object]]:
    """A one-leaf answer for a question that is only a tool value:
    ``(text, tool value, tool result)``, or ``None``."""
    tv = read_value(phrase)
    if tv is None:
        return None
    try:
        value, got = evaluate(tv)
    except ValueError:
        return None
    return (f"{_strip(phrase)} is {_render(value)}, selected "
            f"({', '.join(map(str, tv.selector))}) from `{tv.tool_text}`: "
            f"{got.text}", tv, got)


# ===========================================================================
# VERDICTS -- a tool's yes/no answer handed on (Phase 138)
# ===========================================================================

@dataclass(frozen=True)
class ToolVerdict:
    """One yes/no question a tool decides: the tool text, the test applied to
    its answer, and the claim in declarative form (the step's label).

    Tests (total over the tool's answer):

    * ``("flag", key)`` -- the tool's boolean figure ``key`` (``reachable``
      of ``tool gates``, ``reached`` of ``tool wiring``).  A gate target the
      tool proves unreachable is ``False`` *with the tool's proved reason*;
      a tool that gives no such figure (a malformed word, an unknown module)
      gives no verdict, so the step is refused rather than read as ``False``;
    * ``("flag-not", key)`` -- its negation;
    * ``("equals", <selector...>, value)`` -- the tool must answer, and the
      verdict is whether the selected number equals ``value``.
    """

    phrase: str
    tool_text: str
    test: Tuple[object, ...]
    claim: str
    pattern: str

    @property
    def tool_name(self) -> str:
        return ToolValue(self.phrase, self.tool_text, (), self.pattern
                         ).tool_name

    def as_list(self) -> List[object]:
        return ["verdict", self.tool_text] + [str(t) for t in self.test]


_MOVES = (r"(?: (?:by|with|using) (?:reversible )?(?:toffoli/fredkin |gate |"
          r"toffoli |fredkin )?(?:gate )?moves)?")


def _reach(m, negate: bool = False, swap: bool = False) -> Tuple[str, tuple,
                                                                  str]:
    a, b = m.group(1), m.group(2)
    src, dst = (a, b) if swap else (b, a)
    claim = f"{dst} is {'unreachable' if negate else 'reachable'} from {src}"
    return (f"tool gates {src} to {dst}",
            ("flag-not" if negate else "flag", "reachable"), claim)


def read_verdict(phrase: str) -> Optional[ToolVerdict]:
    """The tool verdict ``phrase`` asks for, or ``None``."""
    t = phrase.strip().rstrip("?.! ").strip()
    t = re.sub(r"^(?:tell me |decide )?(?:whether |if )?", "", t,
               flags=re.IGNORECASE)
    low = t.lower()
    reach = (
        (r"is (\S+) reachable from (\S+)" + _MOVES, False, False),
        (r"is (\S+) unreachable from (\S+)" + _MOVES, True, False),
        (r"can (\S+) reach (\S+)" + _MOVES, False, True),
        (r"(\S+) is reachable from (\S+)" + _MOVES, False, False),
        (r"(\S+) is unreachable from (\S+)" + _MOVES, True, False),
    )
    for pat, neg, swap in reach:
        m = re.fullmatch(pat, low)
        if m:
            text, test, claim = _reach(m, neg, swap)
            return ToolVerdict(phrase, text, test, claim, "reach")
    m = re.fullmatch(r"(?:is )?(?:the )?(?:reasoning )?(?:module )?(\w+)"
                     r"(?: module)? (?:is )?(reached|unreached|wired|unwired)"
                     r"(?: by (?:a|any) query)?", low)
    if m and not re.fullmatch(r"\d+", m.group(1)):
        neg = m.group(2) in ("unreached", "unwired")
        return ToolVerdict(phrase, f"tool wiring {m.group(1)}",
                           ("flag-not" if neg else "flag", "reached"),
                           f"the module {m.group(1)} is "
                           f"{'not ' if neg else ''}reached by a query",
                           "wiring")
    # "is N <tool value>" / "N is <tool value>"
    m = re.fullmatch(r"(?:is )?(-?\d+(?:/\d+)?) (?:is )?(?:equal to )?(the .+)",
                     low)
    if m:
        tv = read_value(m.group(2))
        if tv is not None:
            return ToolVerdict(phrase, tv.tool_text,
                               ("equals",) + tuple(tv.selector)
                               + (m.group(1),),
                               f"{m.group(1)} is {_strip(m.group(2))}",
                               "equals-" + tv.pattern)
    # "is <tool value> equal to N" / "<tool value> is equal to N"
    m = re.fullmatch(r"(?:is )?(.+?) (?:is )?(?:equal to|exactly|the same as) "
                     r"(-?\d+(?:/\d+)?)", low)
    if m:
        tv = read_value(m.group(1))
        if tv is not None:
            return ToolVerdict(phrase, tv.tool_text,
                               ("equals",) + tuple(tv.selector)
                               + (m.group(2),),
                               f"{_strip(m.group(1))} is {m.group(2)}",
                               "equals-" + tv.pattern)
    return None


def decide(verdict: ToolVerdict):
    """``("True" | "False", tool_result)``; raises ``ValueError`` when the
    tool gives no verdict (an ``equals`` test on a tool that refuses)."""
    from . import toolbox as tb
    got = tb.run_tool(verdict.tool_text)
    try:
        return verdict_of_figures(got.ok, got.figures, verdict.test), got
    except ValueError:
        raise ValueError(got.text)


def verdict_of_figures(ok: bool, figures: Mapping[str, object],
                       test: Sequence[object]) -> str:
    """The verdict ``test`` gives on a tool answer -- the rule both
    :func:`decide` and the column-3 script apply."""
    kind = test[0]
    if kind in ("flag", "flag-not"):
        flag = figures.get(str(test[1]))
        if not isinstance(flag, bool):
            raise ValueError("the tool gives no verdict")
        return str(flag if kind == "flag" else not flag)
    if kind == "equals":
        if not ok:
            raise ValueError("the tool refuses")
        return str(select(figures, test[1:-1]) == Fraction(str(test[-1])))
    raise ValueError(f"no verdict test {kind!r}")
