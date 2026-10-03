"""``glm_universal.reasoning.reverse_tct`` -- Reverse Three Column Thinking.

Forward Three Column Thinking goes language -> mathematics -> script, and its
column 1 is a template caption nothing can read back.  This module runs the
other way: the **mathematics** (column 2), given directly or read off a
program in the Phase 64 dialect's syntax (column 3), **generates** the
language column through a declared grammar, and a declared reader parses the
generated sentence back.  ``studies/REVERSE_TCT_STUDY.md`` §1 is the grammar;
``RequestProject/GLM/ReverseTCT.lean`` proves it uniquely readable.

Because column 1 is then a function of column 2 with a left inverse,
operations taken on the mathematics can be *realised back into language*
with the operation's certificate attached -- the extended semantic
operations:

``say``         generate column 1 for a program, term or statement;
``equivalent``  decide whether two sentences mean the same (``SAME`` /
                ``DIFFERENT``);
``paraphrase``  generate equivalent sentences, each certified;
``negate``      the sentence true exactly where a relation is false;
``solve``       ``x equals ...`` (or a bound on ``x``) from a linear
                statement;
``entails``     ``ENTAILS`` / ``CONTRADICTS`` / ``INDEPENDENT`` over ℚ with a
                Farkas certificate or witness points;
``bounds``      the tightest bounds on a variable the premises imply.

Round two (Phase 68, ``studies/REVERSE_TCT_STUDY.md`` §7) widens the fragment
toward the Phase 64 dialect -- floor quotient, remainder, absolute value,
minimum, maximum, negative powers, the bitwise operators and shifts on the
integers, and Golay masks as a second sort -- and adds disjunction, so a
statement is a conjunctive normal form and ``negate`` is total (De Morgan,
then distribution).  Linear decisions split disjunctions and ``abs``/``min``/
``max`` into cases.  ``relay:`` -- handing column 2 to the planner and reading
its answer back -- is read here and answered by
:mod:`glm_universal.runtime.reverse_relay`.

Exact throughout: ``Fraction`` and ``int`` only, no float, no clock, no
randomness.  The column-3 script that checks column 1 is rendered by
:mod:`glm_universal.reasoning.reverse_tct_script` and run by
:mod:`glm_universal.runtime.python_tct` (the reasoning layer does not start
processes).
"""

from __future__ import annotations

import ast
import itertools
import json
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "ReverseRefusal", "realise", "realise_term", "read", "read_term",
    "from_source", "parse_any", "number_words", "evaluate", "poly_of",
    "canonical_term", "say", "equivalent", "paraphrase", "negate", "solve",
    "entails", "bounds", "Answer", "answer", "reads", "OPERATIONS",
    "RESERVED", "holds", "sort_of", "check_sorts", "negation_of",
    "simplify_clauses",
]


class ReverseRefusal(ValueError):
    """A named refusal: ``name`` is one of the study's declared names."""

    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"{name}: {reason}")
        self.name = name
        self.reason = reason


# ===========================================================================
# 1.  NUMBER WORDS
# ===========================================================================

_UNITS = ("zero", "one", "two", "three", "four", "five", "six", "seven",
          "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
          "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
         "eighty", "ninety")
_SCALES = ((10 ** 9, "billion"), (10 ** 6, "million"), (10 ** 3, "thousand"))
WORD_LIMIT = 10 ** 12


def _under_hundred(n: int) -> List[str]:
    if n < 20:
        return [_UNITS[n]]
    t, u = divmod(n, 10)
    return [_TENS[t] if u == 0 else f"{_TENS[t]}-{_UNITS[u]}"]


def _under_thousand(n: int) -> List[str]:
    h, r = divmod(n, 100)
    out: List[str] = []
    if h:
        out += [_UNITS[h], "hundred"]
    if r:
        out += _under_hundred(r)
    return out


def number_words(n: int) -> List[str]:
    """The words of a natural number: ``123456`` is *one hundred twenty-three
    thousand four hundred fifty-six*; digits from 10¹² on."""
    if n < 0:
        raise ValueError("number_words takes a natural number")
    if n >= WORD_LIMIT:
        return [str(n)]
    if n == 0:
        return ["zero"]
    out: List[str] = []
    for size, word in _SCALES:
        q, n = divmod(n, size)
        if q:
            out += _under_thousand(q) + [word]
    if n:
        out += _under_thousand(n)
    return out


_NUMBER_WORDS = set(_UNITS) | {t for t in _TENS if t} | {
    f"{t}-{u}" for t in _TENS if t for u in _UNITS[1:10]} | {
    "hundred", "thousand", "million", "billion"}


def _word_value(w: str) -> Optional[int]:
    if w in _UNITS:
        return _UNITS.index(w)
    if w in _TENS and w:
        return 10 * _TENS.index(w)
    if "-" in w:
        a, b = w.split("-", 1)
        if a in _TENS and a and b in _UNITS[1:10]:
            return 10 * _TENS.index(a) + _UNITS.index(b)
    return None


def _read_natural(toks: Sequence[str], i: int) -> Tuple[int, int]:
    """Read one natural number at ``toks[i]``; accept only the canonical
    spelling (the one :func:`number_words` produces)."""
    if i >= len(toks):
        raise ReverseRefusal("UNREADABLE", "a number was expected at the end")
    t = toks[i]
    if t.isdigit():
        n = int(t)
        if str(n) != t or n < WORD_LIMIT:
            raise ReverseRefusal("UNREADABLE", f"{t!r} is not the canonical "
                                 "spelling of a number")
        return n, i + 1
    if t not in _NUMBER_WORDS or t in ("hundred", "thousand", "million",
                                       "billion"):
        raise ReverseRefusal("UNREADABLE", f"a number was expected at {t!r}")
    j = i
    while j < len(toks) and toks[j] in _NUMBER_WORDS:
        j += 1
    # longest canonical prefix of the number-word run
    for end in range(j, i, -1):
        words = list(toks[i:end])
        total, group, ok = 0, 0, True
        for w in words:
            if w == "hundred":
                group *= 100
            elif w in ("thousand", "million", "billion"):
                total += group * dict((b, a) for a, b in _SCALES)[w]
                group = 0
            else:
                v = _word_value(w)
                if v is None:
                    ok = False
                    break
                group += v
        if not ok:
            continue
        n = total + group
        if number_words(n) == words:
            return n, end
    raise ReverseRefusal("UNREADABLE", f"{' '.join(toks[i:j])!r} is not the "
                         "canonical spelling of a number")


# ===========================================================================
# 2.  THE GRAMMAR -- REALISER (column 2 -> column 1)
# ===========================================================================

#: Binary term heads: the words between ``the`` and ``of``.  Phase 67's four,
#: and round two's (``studies/REVERSE_TCT_STUDY.md`` §7.1).
_BIN_WORDS: Dict[str, Tuple[str, ...]] = {
    "add": ("sum",), "sub": ("difference",), "mul": ("product",),
    "div": ("quotient",),
    "floordiv": ("floor", "quotient"), "mod": ("remainder",),
    "min": ("minimum",), "max": ("maximum",),
    "band": ("bitwise", "and"), "bor": ("bitwise", "or"),
    "bxor": ("exclusive", "or"),
    "lshift": ("left", "shift"), "rshift": ("right", "shift"),
    "inter": ("intersection",), "union": ("union",),
    "symdiff": ("symmetric", "difference"), "setdiff": ("set", "difference"),
    "dist": ("distance",),
}
#: Unary term heads.
_UN_WORDS: Dict[str, Tuple[str, ...]] = {
    "neg": ("negation",), "abs": ("absolute", "value"),
    "compl": ("complement",), "size": ("size",),
}
#: Phase 67's names, kept for the modules that import them.
_BINARY = {"add": "sum", "sub": "difference", "mul": "product",
           "div": "quotient"}
_BINARY_BACK = {v: k for k, v in _BINARY.items()}

#: The sort of each operator's arguments and result: ``n`` a number, ``m`` a
#: Golay mask.
_BIN_SORT: Dict[str, Tuple[str, str, str]] = {
    k: ("n", "n", "n") for k in ("add", "sub", "mul", "div", "floordiv",
                                 "mod", "min", "max", "band", "bor", "bxor",
                                 "lshift", "rshift")}
_BIN_SORT.update({k: ("m", "m", "m") for k in ("inter", "union", "symdiff",
                                               "setdiff")})
_BIN_SORT["dist"] = ("m", "m", "n")
_UN_SORT: Dict[str, Tuple[str, str]] = {"neg": ("n", "n"), "abs": ("n", "n"),
                                        "compl": ("n", "n"),
                                        "size": ("m", "n")}
#: The piecewise-linear operators a linear decision splits into cases.
_PIECEWISE = ("abs", "min", "max")
#: Operators with no finite piecewise-linear reading over a variable.
_NONLINEAR_OPS = ("floordiv", "mod", "band", "bor", "bxor", "lshift",
                  "rshift", "compl")

_RELATIONS = {"=": ["equals"], "!=": ["does", "not", "equal"],
              "<": ["is", "less", "than"], "<=": ["is", "at", "most"],
              ">": ["is", "greater", "than"], ">=": ["is", "at", "least"],
              "in": ["is", "in"], "notin": ["is", "not", "in"],
              "sub": ["is", "contained", "in"],
              "notsub": ["is", "not", "contained", "in"]}
_NEGATION = {"=": "!=", "!=": "=", "<": ">=", "<=": ">", ">": "<=",
             ">=": "<", "in": "notin", "notin": "in", "sub": "notsub",
             "notsub": "sub"}
_CONVERSE = {"=": "=", "!=": "!=", "<": ">", "<=": ">=", ">": "<",
             ">=": "<="}
#: Relation sorts: (left, right).
_REL_SORT = {"<": ("n", "n"), "<=": ("n", "n"), ">": ("n", "n"),
             ">=": ("n", "n"), "in": ("n", "m"), "notin": ("n", "m"),
             "sub": ("m", "m"), "notsub": ("m", "m")}

#: Golay positions a mask may hold.
MASK_POSITIONS = 24
#: Largest shift the realiser evaluates.
SHIFT_LIMIT = 4096

#: Words no variable may be named: every grammar word and number word.
RESERVED = frozenset({
    "the", "of", "and", "square", "cube", "power", "with", "exponent",
    "fraction", "over", "negative", "equals", "does", "not", "equal", "is",
    "less", "than", "at", "most", "greater", "least", "let", "be", "result",
    "nothing", "bounds", "either", "or", "in", "contained", "between",
    "mask", "empty", "position", "positions"}
    | {w for ws in _BIN_WORDS.values() for w in ws}
    | {w for ws in _UN_WORDS.values() for w in ws} | _NUMBER_WORDS)


def _lit_words(q: Fraction) -> List[str]:
    if q.denominator == 1:
        n = q.numerator
        return number_words(n) if n >= 0 else ["negative"] + number_words(-n)
    p = q.numerator
    pw = number_words(p) if p >= 0 else ["negative"] + number_words(-p)
    return ["the", "fraction"] + pw + ["over"] + number_words(q.denominator)


def _mask_words(ps: Sequence[int]) -> List[str]:
    if not ps:
        return ["the", "empty", "mask"]
    out = ["the", "mask", "of"] + number_words(len(ps)) + [
        "position" if len(ps) == 1 else "positions"]
    for i, p in enumerate(ps):
        if i:
            out.append(",")
        out += number_words(p)
    return out


def realise_term(t) -> List[str]:
    """Column 1 of one term, as a token list (prefix first, so unambiguous)."""
    k = t[0]
    if k == "lit":
        return _lit_words(t[1])
    if k == "var":
        return [t[1]]
    if k == "mask":
        return _mask_words(t[1])
    if k in _BIN_WORDS:
        link = "between" if k == "dist" else "of"
        return (["the", *_BIN_WORDS[k], link] + realise_term(t[1]) + ["and"]
                + realise_term(t[2]))
    if k in _UN_WORDS:
        return ["the", *_UN_WORDS[k], "of"] + realise_term(t[1])
    if k == "pow":
        n = t[2]
        if n == 2:
            return ["the", "square", "of"] + realise_term(t[1])
        if n == 3:
            return ["the", "cube", "of"] + realise_term(t[1])
        tail = (["negative"] + number_words(-n)) if n < 0 else number_words(n)
        return (["the", "power", "of"] + realise_term(t[1])
                + ["with", "exponent"] + tail)
    raise ValueError(f"not a term: {t!r}")


def _clauses(s) -> List[List[tuple]]:
    """A statement in conjunctive normal form: a list of clauses, each a list
    of relations (a disjunction)."""
    if s[0] == "rel":
        return [[s]]
    if s[0] == "or":
        return [list(s[1])]
    if s[0] == "and":
        out = []
        for c in s[1]:
            out += _clauses(c)
        return out
    if s[0] == "free":
        return []
    raise ValueError(f"not a statement: {s!r}")


def _from_clauses(clauses: Sequence[Sequence[tuple]]):
    """The canonical statement of a list of clauses."""
    items = [c[0] if len(c) == 1 else ("or", tuple(c)) for c in clauses]
    if not items:
        raise ReverseRefusal("NOT_IN_FRAGMENT", "the empty statement")
    return items[0] if len(items) == 1 else ("and", tuple(items))


def _realise_clause(c) -> List[str]:
    if c[0] == "rel":
        return realise_term(c[2]) + _RELATIONS[c[1]] + realise_term(c[3])
    out = ["either"]
    for i, r in enumerate(c[1]):
        if i:
            out += [",", "or"]
        out += _realise_clause(r)
    return out


def _realise_statement(s) -> List[str]:
    if s[0] in ("rel", "or"):
        return _realise_clause(s)
    if s[0] == "and":
        out: List[str] = []
        for i, r in enumerate(s[1]):
            if i:
                out += [",", "and"]
            out += _realise_clause(r)
        return out
    if s[0] == "free":
        return ["nothing", "bounds", s[1]]
    raise ValueError(f"not a statement: {s!r}")


def _join(toks: Sequence[str]) -> str:
    out = ""
    for t in toks:
        if t in (",", "."):
            out += t
        else:
            out += (" " if out else "") + t
    return out


def realise(obj) -> str:
    """Column 1 of a term, a statement or a program, as one string."""
    k = obj[0]
    if k in ("rel", "and", "or", "free"):
        return _join(_realise_statement(obj))
    if k == "prog":
        toks: List[str] = []
        for name, term in obj[1]:
            toks += ["let", name, "be"] + realise_term(term) + ["."]
        toks += ["the", "result", "is"] + realise_term(obj[2]) + ["."]
        return _join(toks)
    return _join(realise_term(obj))


# ===========================================================================
# 3.  THE GRAMMAR -- READER (column 1 -> column 2)
# ===========================================================================

def _tokens(text: str) -> List[str]:
    out: List[str] = []
    for w in text.replace(",", " , ").replace(".", " . ").split():
        out.append(w)
    return out


_BIN_BACK = sorted(((ws, k) for k, ws in _BIN_WORDS.items()),
                   key=lambda x: -len(x[0]))
_UN_BACK = sorted(((ws, k) for k, ws in _UN_WORDS.items()),
                  key=lambda x: -len(x[0]))


class _Reader:
    def __init__(self, toks: Sequence[str]) -> None:
        self.toks = list(toks)
        self.i = 0

    def peek(self, k: int = 0) -> Optional[str]:
        j = self.i + k
        return self.toks[j] if j < len(self.toks) else None

    def ahead(self, words: Sequence[str], offset: int = 0) -> bool:
        j = self.i + offset
        return self.toks[j:j + len(words)] == list(words)

    def expect(self, *words: str) -> None:
        for w in words:
            if self.peek() != w:
                raise ReverseRefusal("UNREADABLE", f"expected {w!r}, found "
                                     f"{self.peek()!r}")
            self.i += 1

    def natural(self) -> int:
        n, self.i = _read_natural(self.toks, self.i)
        return n

    def mask(self):
        self.expect("the", "mask", "of")
        k = self.natural()
        if k == 0:
            raise ReverseRefusal("UNREADABLE", "an empty mask is spelled "
                                 "'the empty mask'")
        self.expect("position" if k == 1 else "positions")
        ps = []
        for j in range(k):
            if j:
                self.expect(",")
            ps.append(self.natural())
        if any(b <= a for a, b in zip(ps, ps[1:])):
            raise ReverseRefusal("UNREADABLE", "the positions of a mask are "
                                 "spelled in increasing order, once each")
        if ps[-1] >= MASK_POSITIONS:
            raise ReverseRefusal("UNREADABLE", "a mask holds positions zero "
                                 "to twenty-three")
        return ("mask", tuple(ps))

    def term(self):
        t = self.peek()
        if t is None:
            raise ReverseRefusal("UNREADABLE", "a term was expected at the "
                                 "end")
        if t == "the":
            head = self.peek(1)
            for ws, k in _BIN_BACK:
                link = "between" if k == "dist" else "of"
                if self.ahead(("the",) + ws + (link,)):
                    self.expect("the", *ws, link)
                    a = self.term()
                    self.expect("and")
                    b = self.term()
                    return (k, a, b)
            for ws, k in _UN_BACK:
                if self.ahead(("the",) + ws + ("of",)):
                    self.expect("the", *ws, "of")
                    return (k, self.term())
            if head in ("square", "cube"):
                self.expect("the", head, "of")
                return ("pow", self.term(), 2 if head == "square" else 3)
            if head == "power":
                self.expect("the", "power", "of")
                a = self.term()
                self.expect("with", "exponent")
                sign = 1
                if self.peek() == "negative":
                    self.expect("negative")
                    sign = -1
                n = self.natural()
                if sign < 0 and n == 0:
                    raise ReverseRefusal("UNREADABLE", "negative zero")
                if sign > 0 and n in (2, 3):
                    raise ReverseRefusal("UNREADABLE", "exponents two and "
                                         "three are spelled square and cube")
                return ("pow", a, sign * n)
            if head == "empty":
                self.expect("the", "empty", "mask")
                return ("mask", ())
            if head == "mask":
                return self.mask()
            if head == "fraction":
                self.expect("the", "fraction")
                sign = 1
                if self.peek() == "negative":
                    self.expect("negative")
                    sign = -1
                p = self.natural()
                self.expect("over")
                q = self.natural()
                f = Fraction(sign * p, q) if q else None
                if (f is None or f.denominator == 1 or f.numerator != sign * p
                        or (sign < 0 and p == 0)):
                    raise ReverseRefusal("UNREADABLE", "a fraction is spelled "
                                         "in lowest terms, not as an integer")
                return ("lit", f)
            raise ReverseRefusal("UNREADABLE", f"no term begins 'the {head}'")
        if t == "negative":
            self.expect("negative")
            n = self.natural()
            if n == 0:
                raise ReverseRefusal("UNREADABLE", "negative zero")
            return ("lit", Fraction(-n))
        if t.isdigit() or t in _NUMBER_WORDS:
            return ("lit", Fraction(self.natural()))
        if t.isidentifier() and t not in RESERVED:
            self.i += 1
            return ("var", t)
        raise ReverseRefusal("UNREADABLE", f"no term begins {t!r}")

    def relation(self) -> str:
        for op, words in sorted(_RELATIONS.items(), key=lambda kv: -len(kv[1])):
            if self.toks[self.i:self.i + len(words)] == words:
                self.i += len(words)
                return op
        raise ReverseRefusal("UNREADABLE", f"a relation was expected at "
                             f"{self.peek()!r}")

    def simple_statement(self):
        if self.peek() == "nothing":
            self.expect("nothing", "bounds")
            v = self.term()
            if v[0] != "var":
                raise ReverseRefusal("UNREADABLE", "nothing bounds a variable")
            return ("free", v[1])
        a = self.term()
        op = self.relation()
        b = self.term()
        return ("rel", op, a, b)

    def clause(self):
        if self.peek() != "either":
            return self.simple_statement()
        self.expect("either")
        rels = [self.simple_statement()]
        while self.peek() == "," and self.peek(1) == "or":
            self.expect(",", "or")
            rels.append(self.simple_statement())
        if len(rels) < 2 or any(r[0] != "rel" for r in rels):
            raise ReverseRefusal("UNREADABLE", "'either' opens a disjunction "
                                 "of at least two relations")
        return ("or", tuple(rels))

    def statement(self):
        parts = [self.clause()]
        while self.peek() == "," and self.peek(1) == "and":
            self.expect(",", "and")
            parts.append(self.clause())
        if len(parts) > 1 and any(p[0] == "free" for p in parts):
            raise ReverseRefusal("UNREADABLE", "'nothing bounds' stands alone")
        return parts[0] if len(parts) == 1 else ("and", tuple(parts))

    def program(self):
        binds = []
        while self.peek() == "let":
            self.expect("let")
            v = self.term()
            if v[0] != "var":
                raise ReverseRefusal("UNREADABLE", "let binds a variable")
            self.expect("be")
            binds.append((v[1], self.term()))
            self.expect(".")
        self.expect("the", "result", "is")
        t = self.term()
        self.expect(".")
        return ("prog", tuple(binds), t)

    def done(self) -> None:
        if self.i != len(self.toks):
            raise ReverseRefusal("UNREADABLE", "the sentence goes on after "
                                 f"it is complete: {' '.join(self.toks[self.i:])!r}")


def read_term(text: str):
    r = _Reader(_tokens(text))
    t = r.term()
    r.done()
    check_sorts(t)
    return t


def read(text: str):
    """Column 2 of a sentence: a program, a statement or a term."""
    toks = _tokens(text)
    if not toks:
        raise ReverseRefusal("UNREADABLE", "the empty sentence")
    last: Optional[ReverseRefusal] = None
    for kind in ("program", "statement", "term"):
        if kind == "program" and not (toks[0] == "let" or toks[:3] == [
                "the", "result", "is"]):
            continue
        r = _Reader(toks)
        try:
            obj = getattr(r, kind)()
            r.done()
        except ReverseRefusal as exc:
            last = exc
            continue
        check_sorts(obj)
        return obj
    raise last if last is not None else ReverseRefusal("UNREADABLE", text)


# -- sorts ---------------------------------------------------------------------

def _mismatch(msg: str) -> ReverseRefusal:
    return ReverseRefusal("SORT_MISMATCH", msg)


def sort_of(t) -> str:
    """``'n'`` for a number, ``'m'`` for a Golay mask; refuses an ill-sorted
    term by name."""
    k = t[0]
    if k in ("lit", "var"):
        return "n"
    if k == "mask":
        return "m"
    if k == "pow":
        if sort_of(t[1]) != "n":
            raise _mismatch("a mask has no power")
        return "n"
    if k in _BIN_SORT:
        sa, sb, out = _BIN_SORT[k]
        if sort_of(t[1]) != sa or sort_of(t[2]) != sb:
            raise _mismatch(f"{' '.join(_BIN_WORDS[k])} takes "
                            f"{'masks' if sa == 'm' else 'numbers'}")
        return out
    if k in _UN_SORT:
        sa, out = _UN_SORT[k]
        if sort_of(t[1]) != sa:
            raise _mismatch(f"{' '.join(_UN_WORDS[k])} takes "
                            f"{'a mask' if sa == 'm' else 'a number'}")
        return out
    raise ValueError(f"not a term: {t!r}")


def check_sorts(obj) -> None:
    """Refuse an ill-sorted term, statement or program (``SORT_MISMATCH``)."""
    k = obj[0]
    if k == "prog":
        for name, term in obj[1]:
            if sort_of(term) != "n":
                raise _mismatch(f"a variable holds a number; {name} would "
                                "hold a mask")
        if sort_of(obj[2]) != "n" and _variables(obj[2]):
            raise _mismatch("a mask term has no variables")
        return
    if k == "free":
        return
    if k in ("rel", "or", "and"):
        for c in _clauses(obj):
            for r in c:
                sa, sb = sort_of(r[2]), sort_of(r[3])
                want = _REL_SORT.get(r[1])
                if want is None:
                    if sa != sb:
                        raise _mismatch("equality relates two terms of one "
                                        "sort")
                elif (sa, sb) != want:
                    raise _mismatch(f"{' '.join(_RELATIONS[r[1]])} relates "
                                    "terms of other sorts")
        return
    sort_of(obj)


# ===========================================================================
# 4.  COLUMN 3 IN -- THE DIALECT'S SYNTAX AS COLUMN 2
# ===========================================================================

def _int_const(node) -> Optional[int]:
    if (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool)):
        return node.value
    if (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)
            and _int_const(node.operand) is not None):
        return -_int_const(node.operand)
    return None


def _nf(msg: str) -> ReverseRefusal:
    return ReverseRefusal("NOT_IN_FRAGMENT", msg)


def _mask_of(node):
    """A ``frozenset()`` / ``frozenset({...})`` / ``frozenset((...))`` of
    integer literals, as a mask literal."""
    if node.keywords or len(node.args) > 1:
        raise _nf("frozenset takes one set or tuple of positions")
    if not node.args:
        return ("mask", ())
    arg = node.args[0]
    if not isinstance(arg, (ast.Set, ast.Tuple)):
        raise _nf("a mask is written frozenset({...}) or frozenset((...))")
    ps = [_int_const(e) for e in arg.elts]
    if any(p is None for p in ps):
        raise _nf("a mask holds integer positions")
    if any(not 0 <= p < MASK_POSITIONS for p in ps):
        raise _nf("a mask holds positions 0 to 23 of the Golay word")
    return ("mask", tuple(sorted(set(ps))))


def _nest(kind: str, items: Sequence, right: bool):
    if right:
        out = items[-1]
        for t in reversed(items[:-1]):
            out = (kind, t, out)
        return out
    out = items[0]
    for t in items[1:]:
        out = (kind, out, t)
    return out


def _call_of(node):
    f = node.func.id if isinstance(node.func, ast.Name) else None
    if f == "Fraction" and not node.keywords and 1 <= len(node.args) <= 2:
        ints = [_int_const(a) for a in node.args]
        if all(v is not None for v in ints):
            if len(ints) == 2 and ints[1] == 0:
                raise ReverseRefusal("DIVISION_BY_ZERO",
                                     "Fraction with denominator zero")
            return ("lit", Fraction(*ints))
        raise _nf("a call other than Fraction(int[, int])")
    if node.keywords:
        raise _nf(f"keyword arguments to {f}")
    if f == "frozenset":
        return _mask_of(node)
    if f == "abs" and len(node.args) == 1:
        return ("abs", _term_of(node.args[0]))
    if f == "len" and len(node.args) == 1:
        return ("size", _term_of(node.args[0]))
    if f == "hamming" and len(node.args) == 2:
        return ("dist", _term_of(node.args[0]), _term_of(node.args[1]))
    if f in ("min", "max", "sum"):
        args = list(node.args)
        if len(args) == 1 and isinstance(args[0], ast.Tuple):
            args = list(args[0].elts)
        elif f == "sum" or len(args) < 2:
            raise _nf(f"{f} of a tuple literal or of two or more terms")
        if not args:
            if f == "sum":
                return ("lit", Fraction(0))
            raise _nf(f"{f} of nothing")
        items = [_term_of(a) for a in args]
        if len(items) == 1:
            return items[0]
        return _nest({"min": "min", "max": "max", "sum": "add"}[f], items,
                     right=(f != "sum"))
    if f == "pow" and len(node.args) in (2, 3):
        n = _int_const(node.args[1])
        if n is None:
            raise _nf("a power's exponent must be a literal integer")
        base = ("pow", _term_of(node.args[0]), n)
        if len(node.args) == 2:
            return base
        if n < 0:
            raise _nf("pow(a, n, m) with a negative n")
        return ("mod", base, _term_of(node.args[2]))
    raise _nf(f"the call {f or type(node.func).__name__}(...)")


_ARITH = {ast.Add: "add", ast.Sub: "sub", ast.Mult: "mul", ast.Div: "div",
          ast.FloorDiv: "floordiv", ast.Mod: "mod", ast.LShift: "lshift",
          ast.RShift: "rshift"}
_BITS = {ast.BitAnd: ("band", "inter"), ast.BitOr: ("bor", "union"),
         ast.BitXor: ("bxor", "symdiff")}


def _term_of(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            return ("lit", Fraction(node.value))
        raise _nf(f"the literal {node.value!r} is not an exact rational")
    if isinstance(node, ast.Name):
        if node.id in RESERVED or not node.id.isidentifier():
            raise _nf(f"{node.id!r} is a grammar word and cannot name a "
                      "variable")
        return ("var", node.id)
    if isinstance(node, ast.Call):
        return _call_of(node)
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            v = _int_const(node)
            if v is not None:
                return ("lit", Fraction(v))
            return ("neg", _term_of(node.operand))
        if isinstance(node.op, ast.Invert):
            return ("compl", _term_of(node.operand))
        raise _nf(f"the unary operator {type(node.op).__name__}")
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Pow):
            n = _int_const(node.right)
            if n is None:
                raise _nf("a power's exponent must be a literal integer")
            return ("pow", _term_of(node.left), n)
        a, b = _term_of(node.left), _term_of(node.right)
        for cls, (num, mask) in _BITS.items():
            if isinstance(node.op, cls):
                sa, sb = sort_of(a), sort_of(b)
                if sa != sb:
                    raise _mismatch("a mask is not a number")
                return (mask if sa == "m" else num, a, b)
        for cls, name in _ARITH.items():
            if isinstance(node.op, cls):
                if (name == "sub" and sort_of(a) == "m"
                        and sort_of(b) == "m"):
                    return ("setdiff", a, b)
                return (name, a, b)
        raise _nf(f"the operator {type(node.op).__name__}")
    raise _nf(f"the construct {type(node).__name__}")


_CMP = {ast.Eq: "=", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
        ast.Gt: ">", ast.GtE: ">=", ast.In: "in", ast.NotIn: "notin"}
#: Most clauses a statement read from the dialect may distribute into.
CLAUSE_LIMIT = 64


def _neg_rel(r):
    return ("rel", _NEGATION[r[1]], r[2], r[3])


def _distribute(cnfs: Sequence[List[List[tuple]]]) -> List[List[tuple]]:
    """The disjunction of conjunctive normal forms, as one: every choice of a
    clause from each, joined."""
    out: List[List[tuple]] = [[]]
    for cnf in cnfs:
        out = [a + b for a in out for b in cnf]
        if len(out) > CLAUSE_LIMIT:
            raise _nf("the statement distributes into more than "
                      f"{CLAUSE_LIMIT} clauses")
    return out


def _cnf_of(node, positive: bool = True) -> Optional[List[List[tuple]]]:
    if isinstance(node, ast.Compare):
        rels = []
        left = node.left
        for op, right in zip(node.ops, node.comparators):
            sym = next((s for c, s in _CMP.items() if isinstance(op, c)), None)
            if sym is None:
                raise _nf(f"the comparison {type(op).__name__}")
            a, b = _term_of(left), _term_of(right)
            if sym in ("<=",) and sort_of(a) == "m" and sort_of(b) == "m":
                sym = "sub"
            elif (sym in ("<", ">", ">=") and "m" in (sort_of(a),
                                                        sort_of(b))):
                raise _nf("of the orders on masks only <= (contained in) "
                          "has a sentence")
            rels.append(("rel", sym, a, b))
            left = right
        if positive:
            return [[r] for r in rels]
        return [[_neg_rel(r) for r in rels]]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        got = _cnf_of(node.operand, not positive)
        if got is None:
            raise _nf("'not' applies to a statement, not a term")
        return got
    if isinstance(node, ast.BoolOp):
        parts = []
        for v in node.values:
            got = _cnf_of(v, positive)
            if got is None:
                raise _nf("'and' and 'or' join statements, not terms")
            parts.append(got)
        conj = isinstance(node.op, ast.And) == positive
        if conj:
            out = [c for p in parts for c in p]
            if len(out) > CLAUSE_LIMIT:
                raise _nf(f"more than {CLAUSE_LIMIT} clauses")
            return out
        return _distribute(parts)
    return None


def _expr_of(node):
    cnf = _cnf_of(node)
    if cnf is None:
        return _term_of(node)
    return _from_clauses(cnf)


def _loads(node) -> set:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def from_source(source: str):
    """Column 2 of a dialect program, expression or comparison."""
    try:
        tree = ast.parse(source.strip())
    except SyntaxError as exc:
        raise _nf(f"not Python: {exc.msg}") from None
    body = tree.body
    if not body:
        raise _nf("the empty program")
    if len(body) == 1 and isinstance(body[0], ast.Expr):
        obj = _expr_of(body[0].value)
        check_sorts(obj)
        return obj
    binds = []
    for st in body[:-1]:
        if not (isinstance(st, ast.Assign) and len(st.targets) == 1):
            raise _nf("a program is assignments to names, then a result")
        target = st.targets[0]
        if isinstance(target, ast.Name):
            pairs = [(target, st.value)]
        elif (isinstance(target, ast.Tuple) and isinstance(st.value, ast.Tuple)
              and len(target.elts) == len(st.value.elts)
              and all(isinstance(e, ast.Name) for e in target.elts)):
            names = {e.id for e in target.elts}
            if any(_loads(v) & names for v in st.value.elts):
                raise _nf("a simultaneous assignment that reads its own "
                          "targets has no sequential reading")
            pairs = list(zip(target.elts, st.value.elts))
        else:
            raise _nf("a program is assignments to names, then a result")
        for name_node, value in pairs:
            name = name_node.id
            if name in RESERVED:
                raise _nf(f"{name!r} is a grammar word")
            binds.append((name, _term_of(value)))
    last = body[-1]
    if not isinstance(last, ast.Expr):
        raise _nf("a program ends with its result expression")
    obj = ("prog", tuple(binds), _term_of(last.value))
    check_sorts(obj)
    return obj


def parse_any(text: str):
    """Column 2 of ``text``, read as a sentence of the grammar if it is one,
    else as dialect source.  Returns ``(object, 'language'|'source')``."""
    try:
        return read(text), "language"
    except ReverseRefusal as exc_lang:
        try:
            return from_source(text), "source"
        except ReverseRefusal as exc_src:
            if exc_src.reason.startswith("not Python"):
                raise exc_lang from None
            raise


# ===========================================================================
# 5.  COLUMN 2 -- EVALUATION AND THE POLYNOMIAL NORMAL FORM
# ===========================================================================

def _integer(v: Fraction, what: str) -> int:
    if not isinstance(v, Fraction) or v.denominator != 1:
        raise ReverseRefusal("NOT_INTEGER", f"{what} acts on integers; "
                             f"{v} is not one")
    return v.numerator


def evaluate(t, env: Dict[str, Fraction]):
    """The exact value of a term: a ``Fraction``, or a ``frozenset`` for a
    mask."""
    k = t[0]
    if k == "lit":
        return t[1]
    if k == "var":
        if t[1] not in env:
            raise ReverseRefusal("NOT_IN_FRAGMENT", f"{t[1]} is unbound")
        return Fraction(env[t[1]])
    if k == "mask":
        return frozenset(t[1])
    if k == "neg":
        return -evaluate(t[1], env)
    if k == "abs":
        return abs(evaluate(t[1], env))
    if k == "compl":
        return Fraction(-_integer(evaluate(t[1], env), "the complement") - 1)
    if k == "size":
        return Fraction(len(evaluate(t[1], env)))
    if k == "pow":
        base = evaluate(t[1], env)
        if t[2] < 0 and base == 0:
            raise ReverseRefusal("DIVISION_BY_ZERO", "zero to a negative "
                                 "power")
        return base ** t[2]
    a, b = evaluate(t[1], env), evaluate(t[2], env)
    if k == "add":
        return a + b
    if k == "sub":
        return a - b
    if k == "mul":
        return a * b
    if k == "min":
        return min(a, b)
    if k == "max":
        return max(a, b)
    if k == "inter":
        return a & b
    if k == "union":
        return a | b
    if k == "symdiff":
        return a.symmetric_difference(b)
    if k == "setdiff":
        return a - b
    if k == "dist":
        return Fraction(len(a.symmetric_difference(b)))
    if k in ("band", "bor", "bxor"):
        word = " ".join(_BIN_WORDS[k])
        x, y = _integer(a, word), _integer(b, word)
        op = {"band": lambda p, q: p & q, "bor": lambda p, q: p | q,
              "bxor": _xor_of}[k]
        return Fraction(op(x, y))
    if k in ("lshift", "rshift"):
        word = " ".join(_BIN_WORDS[k])
        x, n = _integer(a, word), _integer(b, word)
        if n < 0:
            raise ReverseRefusal("NEGATIVE_SHIFT", "a shift by a negative "
                                 "count")
        if n > SHIFT_LIMIT:
            raise ReverseRefusal("NOT_IN_FRAGMENT", f"a shift by more than "
                                 f"{SHIFT_LIMIT}")
        return Fraction(x * 2 ** n) if k == "lshift" else Fraction(
            x // 2 ** n)
    if b == 0:
        raise ReverseRefusal("DIVISION_BY_ZERO", "a quotient by zero")
    if k == "div":
        return a / b
    if k == "floordiv":
        return Fraction(a // b)
    if k == "mod":
        return a % b
    raise ValueError(f"not a term: {t!r}")


def _xor_of(p: int, q: int) -> int:
    """Exclusive or of two integers (two's complement), written without the
    caret so the combiner's XOR inventory is not widened."""
    return (p | q) & ~(p & q)


_HOLDS = {"=": lambda p, q: p == q, "!=": lambda p, q: p != q,
          "<": lambda p, q: p < q, "<=": lambda p, q: p <= q,
          ">": lambda p, q: p > q, ">=": lambda p, q: p >= q}


def holds(s, env) -> bool:
    if s[0] == "free":
        return True
    if s[0] == "and":
        return all(holds(r, env) for r in s[1])
    if s[0] == "or":
        return any(holds(r, env) for r in s[1])
    a, b = evaluate(s[2], env), evaluate(s[3], env)
    op = s[1]
    if op in ("in", "notin"):
        return (a in b) == (op == "in")
    if op in ("sub", "notsub"):
        return (a <= b) == (op == "sub")
    return _HOLDS[op](a, b)


Mono = Tuple[Tuple[str, int], ...]
Poly = Dict[Mono, Fraction]


def _padd(p: Poly, q: Poly, sign: int = 1) -> Poly:
    out = dict(p)
    for m, c in q.items():
        out[m] = out.get(m, Fraction(0)) + sign * c
        if out[m] == 0:
            del out[m]
    return out


def _mono_mul(a: Mono, b: Mono) -> Mono:
    d: Dict[str, int] = dict(a)
    for v, e in b:
        d[v] = d.get(v, 0) + e
    return tuple(sorted(d.items()))


def _pmul(p: Poly, q: Poly) -> Poly:
    out: Poly = {}
    for m1, c1 in p.items():
        for m2, c2 in q.items():
            m = _mono_mul(m1, m2)
            out[m] = out.get(m, Fraction(0)) + c1 * c2
            if out[m] == 0:
                del out[m]
    return out


def poly_of(t) -> Poly:
    """The polynomial normal form of a term over ℚ; division only by a
    nonzero constant.  A closed subterm is folded to its value first."""
    k = t[0]
    if k == "lit":
        return {(): t[1]} if t[1] else {}
    if k == "var":
        return {((t[1], 1),): Fraction(1)}
    if not _variables(t):
        v = evaluate(t, {})
        if not isinstance(v, Fraction):
            raise _mismatch("a mask is not a number")
        return {(): v} if v else {}
    if k == "neg":
        return _padd({}, poly_of(t[1]), -1)
    if k == "pow":
        if t[2] < 0:
            raise ReverseRefusal("NOT_POLYNOMIAL", "a negative power of a "
                                 "term with a variable is not a polynomial")
        out: Poly = {(): Fraction(1)}
        base = poly_of(t[1])
        for _ in range(t[2]):
            out = _pmul(out, base)
        return out
    if k in _PIECEWISE or k in _NONLINEAR_OPS:
        words = " ".join(_BIN_WORDS.get(k) or _UN_WORDS[k])
        raise ReverseRefusal("NOT_POLYNOMIAL", f"the {words} of a term with "
                             "a variable is not a polynomial")
    if k not in ("add", "sub", "mul", "div"):
        raise _mismatch("a mask is not a number")
    a, b = poly_of(t[1]), poly_of(t[2])
    if k == "add":
        return _padd(a, b)
    if k == "sub":
        return _padd(a, b, -1)
    if k == "mul":
        return _pmul(a, b)
    if not b:
        raise ReverseRefusal("DIVISION_BY_ZERO", "a quotient by a term that "
                             "is identically zero")
    if set(b) != {()}:
        raise ReverseRefusal("NOT_POLYNOMIAL", "a quotient by a term with a "
                             "variable is not a polynomial")
    c = b[()]
    return {m: v / c for m, v in a.items()}


def degree(p: Poly) -> int:
    return max((sum(e for _, e in m) for m in p), default=0)


def _mono_key(m: Mono):
    return (-sum(e for _, e in m), m)


def _mono_term(m: Mono):
    t = None
    for v, e in m:
        f = ("var", v) if e == 1 else ("pow", ("var", v), e)
        t = f if t is None else ("mul", t, f)
    return t


def canonical_term(p: Poly):
    """The declared canonical term of a polynomial: monomials by descending
    degree then by variable, constant last; a later negative monomial is a
    difference."""
    monos = sorted(p, key=_mono_key)
    if not monos:
        return ("lit", Fraction(0))
    out = None
    for m in monos:
        c = p[m]
        if out is None:
            if m == ():
                out = ("lit", c)
            elif c == 1:
                out = _mono_term(m)
            elif c == -1:
                out = ("neg", _mono_term(m))
            else:
                out = ("mul", ("lit", c), _mono_term(m))
            continue
        a = abs(c)
        body = ("lit", a) if m == () else (
            _mono_term(m) if a == 1 else ("mul", ("lit", a), _mono_term(m)))
        out = ("add" if c > 0 else "sub", out, body)
    return out


def _variables(obj) -> List[str]:
    out = set()

    def walk(x):
        if isinstance(x, tuple):
            if len(x) == 2 and x[0] == "var":
                out.add(x[1])
            elif x and x[0] == "free":
                out.add(x[1])
            else:
                for y in x:
                    walk(y)
    walk(obj)
    return sorted(out)


def _conjuncts(s) -> List:
    """The clauses of a statement as statements (a relation or an ``or``)."""
    if s[0] == "and":
        return list(s[1])
    return [s]


# ===========================================================================
# 6.  LINEAR ARITHMETIC OVER ℚ -- FOURIER-MOTZKIN WITH FARKAS MULTIPLIERS
# ===========================================================================

@dataclass(frozen=True)
class Row:
    """``sum(coeffs[v] * v) + const  <  0`` (strict) or ``<= 0``."""

    coeffs: Tuple[Tuple[str, Fraction], ...]
    const: Fraction
    strict: bool


def _linear(t) -> Tuple[Dict[str, Fraction], Fraction]:
    p = poly_of(t)
    if degree(p) > 1:
        raise ReverseRefusal("NONLINEAR", f"{realise(t)!r} has degree "
                             f"{degree(p)}")
    coeffs = {m[0][0]: c for m, c in p.items() if m}
    return coeffs, p.get((), Fraction(0))


def _rel_rows(op: str, a, b) -> List[Row]:
    """Rows for a relation whose op is one of ``< <= > >= =`` (not !=)."""
    ca, ka = _linear(a)
    cb, kb = _linear(b)
    diff = dict(ca)
    for v, c in cb.items():
        diff[v] = diff.get(v, Fraction(0)) - c
    diff = {v: c for v, c in diff.items() if c}
    k = ka - kb

    def row(sign: int, strict: bool) -> Row:
        return Row(tuple(sorted((v, sign * c) for v, c in diff.items())),
                   sign * k, strict)
    if op == "<":
        return [row(1, True)]
    if op == "<=":
        return [row(1, False)]
    if op == ">":
        return [row(-1, True)]
    if op == ">=":
        return [row(-1, False)]
    if op == "=":
        return [row(1, False), row(-1, False)]
    raise ValueError(op)


#: Most cases a linear decision may split into.
CASE_LIMIT = 4096
_ZERO = ("lit", Fraction(0))


def _pw_node(t):
    """The first ``abs``/``min``/``max`` node over a variable in ``t``,
    pre-order, or ``None``."""
    if not isinstance(t, tuple) or not t or t[0] in ("lit", "var", "mask"):
        return None
    if t[0] in _PIECEWISE and _variables(t):
        return t
    for x in t[1:]:
        if isinstance(x, tuple):
            got = _pw_node(x)
            if got is not None:
                return got
    return None


def _replace(t, node, by):
    if t == node:
        return by
    if not isinstance(t, tuple) or not t or t[0] in ("lit", "var", "mask"):
        return t
    return tuple(_replace(x, node, by) if isinstance(x, tuple) else x
                 for x in t)


def _branches(n):
    """The two pieces of a piecewise node: ``(condition, replacement)``."""
    if n[0] == "abs":
        return [((">=", n[1], _ZERO), n[1]), (("<", n[1], _ZERO),
                                              ("neg", n[1]))]
    if n[0] == "min":
        return [(("<=", n[1], n[2]), n[1]), ((">", n[1], n[2]), n[2])]
    return [((">=", n[1], n[2]), n[1]), (("<", n[1], n[2]), n[2])]


def _expand_pieces(case: List[Tuple[str, object, object]]):
    """Split a case at its first piecewise node, recursively: the splitting
    condition joins the case, and the node is replaced by its piece in every
    relation of the case."""
    for op, a, b in case:
        n = _pw_node(a) or _pw_node(b)
        if n is not None:
            break
    else:
        return [case]
    out = []
    for cond, by in _branches(n):
        new = [(op, _replace(a, n, by), _replace(b, n, by))
               for op, a, b in case]
        out += _expand_pieces(new + [cond])
        if len(out) > CASE_LIMIT:
            raise _nf("the system splits into too many cases")
    return out


def _cases(stmts: Sequence) -> List[List[Tuple[str, object, object]]]:
    """The case systems of a list of statements: one relation chosen from
    each clause, ``!=`` split into ``<`` or ``>``, and every piecewise node
    split into its pieces.  Each is a list of ``(op, lhs, rhs)`` with op in
    ``< <= > >= =``; the statements hold at a point iff some case does."""
    choices = []
    for s in stmts:
        for clause in _clauses(s):
            alts = []
            for r in clause:
                if r[1] == "!=":
                    alts += [("<", r[2], r[3]), (">", r[2], r[3])]
                else:
                    alts.append((r[1], r[2], r[3]))
            choices.append(alts)
    out = []
    for combo in itertools.product(*choices):
        out += _expand_pieces(list(combo))
        if len(out) > CASE_LIMIT:
            raise _nf("the system splits into too many cases")
    return out


def _check_linear(s) -> None:
    """Refuse a statement a linear decision cannot take: a mask statement
    (``NOT_IN_FRAGMENT``), or a case with a nonlinear or non-polynomial
    side."""
    for c in _clauses(s):
        for r in c:
            if r[1] in _REL_SORT and _REL_SORT[r[1]] != ("n", "n") or \
                    "m" in (sort_of(r[2]), sort_of(r[3])):
                raise _nf("a mask statement is closed: say decides it")
    for case in _cases([s]):
        for _, a, b in case:
            _linear(a)
            _linear(b)


def _fm(rows: List[Row], order: Sequence[str]):
    """Fourier-Motzkin elimination with Farkas multipliers.

    Returns ``("sat", witness)`` or ``("unsat", multipliers)`` where the
    multipliers are non-negative weights on ``rows`` whose combination has
    every coefficient zero and a contradictory constant.
    """
    n = len(rows)
    cur = [(dict(r.coeffs), r.const, r.strict, {i: Fraction(1)})
           for i, r in enumerate(rows)]
    stages = []
    for v in order:
        stages.append((v, cur))
        pos = [r for r in cur if r[0].get(v, 0) > 0]
        neg = [r for r in cur if r[0].get(v, 0) < 0]
        nxt = [r for r in cur if r[0].get(v, 0) == 0]
        for p in pos:
            for q in neg:
                a, b = -q[0][v], p[0][v]
                co: Dict[str, Fraction] = {}
                for w in set(p[0]) | set(q[0]):
                    c = a * p[0].get(w, 0) + b * q[0].get(w, 0)
                    if c:
                        co[w] = Fraction(c)
                lam: Dict[int, Fraction] = {}
                for i, x in p[3].items():
                    lam[i] = lam.get(i, Fraction(0)) + a * x
                for i, x in q[3].items():
                    lam[i] = lam.get(i, Fraction(0)) + b * x
                nxt.append((co, a * p[1] + b * q[1], p[2] or q[2], lam))
                if len(nxt) > 20000:
                    raise ReverseRefusal("NOT_IN_FRAGMENT", "the system is "
                                         "too large to eliminate")
        cur = nxt
    for co, k, strict, lam in cur:
        if co:
            continue
        if k > 0 or (strict and k >= 0):
            return "unsat", {i: lam.get(i, Fraction(0)) for i in range(n)}
    # back-substitute a witness
    point: Dict[str, Fraction] = {}
    for v, rs in reversed(stages):
        lo, lo_s, hi, hi_s = None, False, None, False
        for co, k, strict, _ in rs:
            c = co.get(v, 0)
            if not c:
                continue
            rest = k + sum(co[w] * point.get(w, Fraction(0))
                           for w in co if w != v)
            bound = Fraction(-rest) / c
            if c > 0:
                if hi is None or bound < hi or (bound == hi and strict):
                    hi, hi_s = bound, strict
            else:
                if lo is None or bound > lo or (bound == lo and strict):
                    lo, lo_s = bound, strict
        if lo is not None and hi is not None:
            val = lo if lo == hi else (lo + hi) / 2
        elif lo is not None:
            val = lo + 1 if lo_s else lo
        elif hi is not None:
            val = hi - 1 if hi_s else hi
        else:
            val = Fraction(0)
        point[v] = val
    return "sat", point


def _system(case) -> List[Row]:
    rows: List[Row] = []
    for op, a, b in case:
        rows += _rel_rows(op, a, b)
    return rows


def _satisfiable(case, variables: Sequence[str]):
    rows = _system(case)
    status, got = _fm(rows, list(variables))
    if status == "sat":
        for v in variables:
            got.setdefault(v, Fraction(0))
        return True, got
    return False, {"rows": case, "multipliers": [got[i] for i in
                                                 range(len(rows))]}


def _consistent(stmts: Sequence, variables: Sequence[str]):
    """``(True, witness)`` or ``(False, [certificate per case])``."""
    certs = []
    for case in _cases(stmts):
        ok, got = _satisfiable(case, variables)
        if ok:
            return True, got
        certs.append(got)
    return False, certs


def _negations(clause) -> List:
    """The negation of one clause (a relation or a disjunction), as the list
    of negated relations it conjoins."""
    return [_neg_rel(r) for r in _clauses(clause)[0]]


# ===========================================================================
# 7.  THE OPERATIONS
# ===========================================================================

@dataclass
class Answer:
    """One operation's answer: the verdict, column 1, column 2, and the
    certificate a column-3 script checks."""

    operation: str
    verdict: str
    sentence: str = ""
    column1: List[str] = field(default_factory=list)
    column2: List[str] = field(default_factory=list)
    certificate: Dict[str, object] = field(default_factory=dict)
    refusal: str = ""
    reason: str = ""

    @property
    def answered(self) -> bool:
        return not self.refusal

    def as_dict(self) -> Dict[str, object]:
        return {"operation": self.operation, "verdict": self.verdict,
                "sentence": self.sentence, "column1": list(self.column1),
                "column2": list(self.column2), "refusal": self.refusal,
                "reason": self.reason}


def _refused(op: str, exc: ReverseRefusal) -> Answer:
    return Answer(op, exc.name, refusal=exc.name, reason=exc.reason,
                  column1=[f"refused: {exc.name}: {exc.reason}"])


_MATH_BIN = {"add": "+", "sub": "-", "mul": "*", "div": "/",
             "floordiv": "//", "mod": "mod", "band": "AND", "bor": "OR",
             "bxor": "XOR", "lshift": "<<", "rshift": ">>", "inter": "∩",
             "union": "∪", "symdiff": "△", "setdiff": "∖"}
_MATH_REL = {"=": "=", "!=": "≠", "<": "<", "<=": "≤", ">": ">", ">=": "≥",
             "in": "∈", "notin": "∉", "sub": "⊆", "notsub": "⊈"}


def _math(obj) -> str:
    """Column 2's infix rendering: fully bracketed, exact."""
    k = obj[0]
    if k == "lit":
        q = obj[1]
        return str(q.numerator) if q.denominator == 1 else f"({q})"
    if k == "var":
        return obj[1]
    if k == "mask":
        return "{" + ", ".join(str(p) for p in obj[1]) + "}"
    if k == "neg":
        return f"-{_math(obj[1])}"
    if k == "abs":
        return f"|{_math(obj[1])}|"
    if k == "compl":
        return f"NOT {_math(obj[1])}"
    if k == "size":
        return f"#{_math(obj[1])}"
    if k == "pow":
        return f"{_math(obj[1])}^{obj[2]}"
    if k in ("min", "max", "dist"):
        name = {"dist": "d"}.get(k, k)
        return f"{name}({_math(obj[1])}, {_math(obj[2])})"
    if k in _MATH_BIN:
        return f"({_math(obj[1])} {_MATH_BIN[k]} {_math(obj[2])})"
    if k == "rel":
        return f"{_math(obj[2])} {_MATH_REL[obj[1]]} {_math(obj[3])}"
    if k == "or":
        return "(" + " ∨ ".join(_math(r) for r in obj[1]) + ")"
    if k == "and":
        return " ∧ ".join(_math(r) for r in obj[1])
    if k == "free":
        return f"{obj[1]} ∈ ℚ"
    if k == "prog":
        return "; ".join([f"{n} := {_math(t)}" for n, t in obj[1]]
                         + [f"result := {_math(obj[2])}"])
    raise ValueError(obj)


def _is_statement(obj) -> bool:
    return obj[0] in ("rel", "and", "or", "free")


def _value_term(v):
    """A value as a closed literal term: a number or a mask."""
    if isinstance(v, frozenset):
        return ("mask", tuple(sorted(v)))
    return ("lit", Fraction(v))


def _rebuild(x, go):
    k = x[0]
    if k == "pow":
        return ("pow", go(x[1]), x[2])
    if k in _UN_WORDS:
        return (k, go(x[1]))
    return (k, go(x[1]), go(x[2]))


def _steps(t, env) -> List[Tuple[str, str]]:
    """Evaluation of a closed term, bottom-up: each step's equation realised
    back into language (column 1 generated from column 2)."""
    out: List[Tuple[str, str]] = []

    def go(x):
        k = x[0]
        if k in ("lit", "mask"):
            return x
        if k == "var":
            return _value_term(evaluate(x, env))
        node = _rebuild(x, go)
        val = _value_term(evaluate(node, {}))
        eq = ("rel", "=", node, val)
        out.append((realise(eq), _math(eq) + " over ℚ"))
        return val
    go(t)
    return out


def _closed_program_value(obj):
    env: Dict[str, Fraction] = {}
    for name, term in obj[1]:
        env[name] = evaluate(term, env)
    return evaluate(obj[2], env)


def say(text: str) -> Answer:
    """Generate column 1 from column 2 (read off source or a sentence).  A
    closed term or program carries its value, a closed statement its truth,
    so the column-3 script can re-derive both."""
    try:
        obj, _ = parse_any(text)
        col1 = [realise(obj)]
        col2 = [_math(obj)]
        verdict = "SAID"
        cert: Dict[str, object] = {"kind": "say", "structure": _enc(obj)}
        if obj[0] == "prog":
            env: Dict[str, Fraction] = {}
            for name, term in obj[1]:
                for lang, m in _steps(term, env):
                    col1.append(lang)
                    col2.append(m)
                env[name] = evaluate(term, env)
                eq = ("rel", "=", ("var", name), _value_term(env[name]))
                col1.append(realise(eq))
                col2.append(_math(eq))
            val = evaluate(obj[2], env)
            if obj[2][0] != "var":
                for lang, m in _steps(obj[2], env):
                    col1.append(lang)
                    col2.append(m)
                eq = ("rel", "=", obj[2], _value_term(val))
                col1.append(realise(eq))
                col2.append(_math(eq))
            cert["value"] = _enc(_value_term(val))
        elif not _variables(obj) and not _is_statement(obj):
            for lang, m in _steps(obj, {}):
                col1.append(lang)
                col2.append(m)
            cert["value"] = _enc(_value_term(evaluate(obj, {})))
        elif not _variables(obj) and obj[0] == "rel":
            a, b = evaluate(obj[2], {}), evaluate(obj[3], {})
            true_op = obj[1] if holds(obj, {}) else _NEGATION[obj[1]]
            eq = ("rel", true_op, _value_term(a), _value_term(b))
            col1.append(realise(eq))
            col2.append(_math(eq))
            verdict = "TRUE" if true_op == obj[1] else "FALSE"
            cert["truth"] = verdict == "TRUE"
        elif not _variables(obj) and obj[0] in ("and", "or"):
            verdict = "TRUE" if holds(obj, {}) else "FALSE"
            cert["truth"] = verdict == "TRUE"
        return Answer("say", verdict, col1[0], col1, col2, cert)
    except ReverseRefusal as exc:
        if exc.name in ("NOT_IN_FRAGMENT", "UNREADABLE"):
            # Phase 94: the third sort (strings, tuples, ranges) is asked
            # only where this grammar refuses, so no earlier answer moves.
            from .reverse_tct_seq import say_third_sort
            got = say_third_sort(text)
            if got is not None:
                return got
            # Phase 95: the imperative grammar, asked only where the third
            # sort cannot read the text either.
            from .reverse_tct_imp import say_imperative
            got = say_imperative(text)
            if got is not None:
                return got
        return _refused("say", exc)


def _normal_rel(r):
    """``(poly items, op)`` with op in ``< <= = !=``, scaled so the leading
    coefficient is 1 (or its absolute value 1 for an inequality)."""
    op = r[1]
    p = _padd(poly_of(r[2]), poly_of(r[3]), -1)
    if op in (">", ">="):
        p = _padd({}, p, -1)
        op = {">": "<", ">=": "<="}[op]
    if p:
        lead = p[sorted(p, key=_mono_key)[0]]
        scale = abs(lead) if op in ("<", "<=") else lead
        p = {m: c / scale for m, c in p.items()}
    return (tuple(sorted(p.items())), op), p


def _pairing(s1, s2):
    """A conjunct-by-conjunct pairing with scales, if the normal forms agree:
    the syntactic (any-degree) certificate of equivalence.  Only for
    conjunctions of numeric order relations with polynomial sides."""
    c1, c2 = _conjuncts(s1), _conjuncts(s2)
    if len(c1) != len(c2) or any(r[0] != "rel" or r[1] not in _HOLDS
                                 for r in c1 + c2):
        return None
    try:
        n2 = [_normal_rel(r)[0] for r in c2]
        n1 = [_normal_rel(r)[0] for r in c1]
    except ReverseRefusal as exc:
        if exc.name in ("NOT_POLYNOMIAL", "SORT_MISMATCH"):
            return None
        raise
    used, pairs = set(), []
    for i, r in enumerate(c1):
        key = n1[i]
        j = next((j for j in range(len(c2)) if j not in used and n2[j] == key),
                 None)
        if j is None:
            return None
        used.add(j)
        d1 = _padd(poly_of(r[2]), poly_of(r[3]), -1)
        d2 = _padd(poly_of(c2[j][2]), poly_of(c2[j][3]), -1)
        if not d1 and not d2:
            k = Fraction(1)
        else:
            m = sorted(d1, key=_mono_key)[0]
            k = d1[m] / d2[m]
        pairs.append([i, j, _q(k)])
    return pairs


def _entails_raw(premises: Sequence, conclusion, variables):
    """Does every point satisfying ``premises`` satisfy ``conclusion``?

    Returns ``(True, certificates)`` (one per clause of the conclusion: the
    conjunction of its negated relations, refuted case by case) or
    ``(False, witness)``.
    """
    certs = []
    for clause in _clauses(conclusion):
        negated = [_neg_rel(r) for r in clause]
        ok, got = _consistent(list(premises) + negated, variables)
        if ok:
            return False, got
        certs.append({"negated": [_enc(n) for n in negated],
                      "cases": _enc_certs(got)})
    return True, certs


def _piecewise_linear(t) -> bool:
    try:
        _check_linear(("rel", "=", t, _ZERO))
    except ReverseRefusal:
        return False
    return True


def equivalent(first: str, second: str) -> Answer:
    op = "equivalent"
    try:
        a, _ = parse_any(first)
        b, _ = parse_any(second)
        if a[0] == "prog" or b[0] == "prog":
            raise _nf("equivalence is of terms or statements, not programs")
        if _is_statement(a) != _is_statement(b):
            raise _nf("a term and a statement cannot mean the same")
        col2 = [_math(a), _math(b)]
        if not _is_statement(a):
            if sort_of(a) != sort_of(b):
                raise _mismatch("a mask and a number cannot mean the same")
            if sort_of(a) == "m":
                same = evaluate(a, {}) == evaluate(b, {})
                cert = {"kind": "term-identity", "first": _enc(a),
                        "second": _enc(b), "same": same}
                if not same:
                    cert["witness"] = {}
            else:
                try:
                    pa, pb = poly_of(a), poly_of(b)
                except ReverseRefusal as exc:
                    if exc.name != "NOT_POLYNOMIAL" or not (
                            _piecewise_linear(a) and _piecewise_linear(b)):
                        raise
                    pa = pb = None
                if pa is not None:
                    same = pa == pb
                    cert = {"kind": "term-identity", "first": _enc(a),
                            "second": _enc(b), "same": same}
                    if not same:
                        cert["witness"] = _enc_point(
                            _nonroot(_padd(pa, pb, -1)))
                else:
                    eq = ("rel", "=", a, b)
                    vs = _variables((a, b))
                    ok, got = _entails_raw([], eq, vs)
                    same = ok
                    cert = {"kind": "term-pieces", "first": _enc(a),
                            "second": _enc(b), "same": same}
                    if ok:
                        cert["entails"] = got
                    else:
                        cert["witness"] = _enc_point(got)
            verdict = "SAME" if same else "DIFFERENT"
        else:
            pairs = _pairing(a, b)
            cert = {"kind": "statement", "first": _enc(a), "second": _enc(b)}
            if pairs is not None:
                verdict = "SAME"
                cert["pairing"] = pairs
            else:
                for s in (a, b):
                    try:
                        _check_linear(s)
                    except ReverseRefusal as exc:
                        if exc.name == "NONLINEAR":
                            raise ReverseRefusal(
                                "NONLINEAR", "the normal forms differ and "
                                "the statements are not linear, so equality "
                                "of meaning is not decided") from None
                        raise
                vs = _variables((a, b))
                ok1, got1 = _entails_raw([a], b, vs)
                ok2, got2 = _entails_raw([b], a, vs)
                if ok1 and ok2:
                    verdict = "SAME"
                    cert["mutual"] = [got1, got2]
                else:
                    verdict = "DIFFERENT"
                    cert["witness"] = _enc_point(got1 if not ok1 else got2)
        word = "mean the same" if verdict == "SAME" else "differ in meaning"
        sentence = f"{realise(a)} ; {realise(b)} : {word}"
        return Answer(op, verdict, sentence, [realise(a), realise(b), word],
                      col2, cert)
    except ReverseRefusal as exc:
        return _refused(op, exc)


def _nonroot(p: Poly) -> Dict[str, Fraction]:
    """A point where a nonzero polynomial is nonzero, on the grid
    ``{0..deg}^n`` (such a point exists)."""
    vs = sorted({v for m in p for v, _ in m})
    d = max(degree(p), 1)
    for pt in itertools.product(range(d + 1), repeat=len(vs)):
        env = dict(zip(vs, (Fraction(x) for x in pt)))
        val = sum((c * _mono_eval(m, env) for m, c in p.items()),
                  Fraction(0))
        if val != 0:
            return env
    raise AssertionError("a nonzero polynomial vanished on its grid")


def _mono_eval(m: Mono, env) -> Fraction:
    out = Fraction(1)
    for v, e in m:
        out *= env[v] ** e
    return out


def negation_of(s):
    """The negation of a statement in conjunctive normal form, again in
    conjunctive normal form: one clause per choice of a relation from each
    clause, each relation negated (De Morgan, then distribution)."""
    clauses = _clauses(s)
    if not clauses:
        raise _nf("'nothing bounds' has no negation in the fragment")
    negs = [[_neg_rel(r) for r in c] for c in clauses]
    if _product_size(negs) > CLAUSE_LIMIT ** 2:
        raise _nf(f"the negation distributes into more than {CLAUSE_LIMIT} "
                  "clauses")
    out = simplify_clauses([list(choice)
                            for choice in itertools.product(*negs)])
    if len(out) > CLAUSE_LIMIT:
        raise _nf(f"the negation distributes into more than {CLAUSE_LIMIT} "
                  "clauses")
    return _from_clauses(out)


def _product_size(lists) -> int:
    n = 1
    for x in lists:
        n *= len(x)
    return n


def simplify_clauses(clauses: Sequence[Sequence[tuple]]) -> List[List[tuple]]:
    """Exact propositional simplification of a conjunctive normal form, in a
    declared order: a relation repeated in a clause is dropped (idempotence);
    a clause holding a relation and its negation is dropped while another
    clause remains (it always holds); a repeated clause is dropped; a clause
    that contains every relation of another clause is dropped (absorption).
    Order is otherwise kept."""
    out: List[List[tuple]] = []
    for c in clauses:
        seen: List[tuple] = []
        for r in c:
            if r not in seen:
                seen.append(r)
        out.append(seen)
    kept = [c for c in out if not any(_neg_rel(r) in c for r in c)]
    out = kept if kept else out[:1]
    uniq: List[List[tuple]] = []
    for c in out:
        if not any(set(c) == set(d) for d in uniq):
            uniq.append(c)
    return [c for i, c in enumerate(uniq)
            if not any(j != i and set(d) < set(c)
                       for j, d in enumerate(uniq))]


def negate(text: str) -> Answer:
    op = "negate"
    try:
        s, _ = parse_any(text)
        if not _is_statement(s):
            raise _nf("negate takes a statement, not a term or a program")
        n = negation_of(s)
        return Answer(op, "NEGATED", realise(n), [realise(s), realise(n)],
                      [_math(s), _math(n)],
                      {"kind": "negate", "first": _enc(s), "second": _enc(n)})
    except ReverseRefusal as exc:
        return _refused(op, exc)


def solve(var: str, text: str) -> Answer:
    op = "solve"
    try:
        s, _ = parse_any(text)
        if s[0] != "rel" or s[1] not in _HOLDS:
            raise _nf("solve takes one numeric relation")
        p = _padd(poly_of(s[2]), poly_of(s[3]), -1)
        if any(e >= 2 for m in p for v, e in m if v == var):
            raise ReverseRefusal("NONLINEAR", f"{var} appears with a power "
                                 "above one")
        coeff: Poly = {}
        rest: Poly = {}
        for m, c in p.items():
            if (var, 1) in m:
                coeff[tuple(x for x in m if x[0] != var)] = c
            else:
                rest[m] = c
        if not coeff:
            raise ReverseRefusal("NO_UNIQUE_SOLUTION", f"{var} does not occur "
                                 "once the statement is normalised")
        if set(coeff) != {()}:
            raise ReverseRefusal("NONCONSTANT_COEFFICIENT", f"the coefficient "
                                 f"of {var} is {realise(canonical_term(coeff))}")
        c = coeff[()]
        sol = canonical_term({m: -v / c for m, v in rest.items()})
        rel = s[1] if c > 0 else _CONVERSE[s[1]]
        out = ("rel", rel, ("var", var), sol)
        cert = {"kind": "statement", "first": _enc(s), "second": _enc(out),
                "pairing": [[0, 0, _q(c)]]}
        return Answer(op, "SOLVED", realise(out), [realise(s), realise(out)],
                      [_math(s), _math(out)], cert)
    except ReverseRefusal as exc:
        return _refused(op, exc)


def _statements(premises: Sequence[str]) -> List:
    out = []
    for p in premises:
        s, _ = parse_any(p)
        if not _is_statement(s):
            raise _nf("a premise is a statement, not a term")
        out.append(s)
    return out


def entails(premises: Sequence[str], conclusion: str) -> Answer:
    op = "entails"
    try:
        ps = _statements(premises)
        c, _ = parse_any(conclusion)
        if not _is_statement(c):
            raise _nf("a conclusion is a statement, not a term")
        for s in ps + [c]:
            _check_linear(s)
        vs = _variables((tuple(ps), c))
        ok, got = _consistent(ps, vs)
        base = {"kind": "entails", "premises": [_enc(s) for s in ps],
                "conclusion": _enc(c)}
        col1 = [realise(s) for s in ps] + [realise(c)]
        col2 = [_math(s) for s in ps] + [_math(c)]
        if not ok:
            exc = ReverseRefusal("INCONSISTENT_PREMISES", "no point satisfies "
                                 "the premises, so every conclusion would "
                                 "follow")
            a = _refused(op, exc)
            a.certificate = dict(base, inconsistent=_enc_certs(got))
            return a
        e_ok, e_got = _entails_raw(ps, c, vs)
        if e_ok:
            verdict, cert = "ENTAILS", dict(base, entails=e_got)
            word = "follows from the premises"
        else:
            c_ok, c_got = _consistent(ps + [c], vs)
            if not c_ok:
                verdict = "CONTRADICTS"
                cert = dict(base, contradicts=_enc_certs(c_got))
                word = "contradicts the premises"
            else:
                verdict = "INDEPENDENT"
                cert = dict(base, holds_at=_enc_point(c_got),
                            fails_at=_enc_point(e_got))
                word = "neither follows from nor contradicts the premises"
        return Answer(op, verdict, f"{realise(c)} : {word}", col1 + [word],
                      col2, cert)
    except ReverseRefusal as exc:
        return _refused(op, exc)


def _project(case, var: str, variables):
    """Bounds on ``var`` in one satisfiable case system."""
    rows = _system(case)
    order = [v for v in variables if v != var]
    # eliminate the others, then read the rows on var alone
    cur = [(dict(r.coeffs), r.const, r.strict) for r in rows]
    for v in order:
        pos = [r for r in cur if r[0].get(v, 0) > 0]
        neg = [r for r in cur if r[0].get(v, 0) < 0]
        nxt = [r for r in cur if r[0].get(v, 0) == 0]
        for p in pos:
            for q in neg:
                a, b = -q[0][v], p[0][v]
                co = {w: a * p[0].get(w, 0) + b * q[0].get(w, 0)
                      for w in set(p[0]) | set(q[0])}
                nxt.append(({w: Fraction(c) for w, c in co.items() if c},
                            a * p[1] + b * q[1], p[2] or q[2]))
        cur = nxt
    lo, lo_s, hi, hi_s = None, False, None, False
    for co, k, strict in cur:
        c = co.get(var, 0)
        if not c:
            continue
        bound = Fraction(-k) / c
        if c > 0:
            if hi is None or bound < hi or (bound == hi and strict):
                hi, hi_s = bound, strict
        else:
            if lo is None or bound > lo or (bound == lo and strict):
                lo, lo_s = bound, strict
    return lo, lo_s, hi, hi_s


def _hull(ends, lower: bool):
    """The end of the union of the cases' intervals: ``None`` if any case
    is unbounded that way; strict only if every case reaching it is."""
    if any(v is None for v, _ in ends):
        return None, False
    best = min(v for v, _ in ends) if lower else max(v for v, _ in ends)
    return best, all(s for v, s in ends if v == best)


def bounds(var: str, premises: Sequence[str]) -> Answer:
    op = "bounds"
    try:
        ps = _statements(premises)
        for s in ps:
            _check_linear(s)
        vs = sorted(set(_variables(tuple(ps))) | {var})
        ok, got = _consistent(ps, vs)
        if not ok:
            raise ReverseRefusal("INCONSISTENT_PREMISES", "no point satisfies "
                                 "the premises")
        lows, highs = [], []
        for case in _cases(ps):
            sat, _ = _satisfiable(case, vs)
            if sat:
                l, ls, h, hs = _project(case, var, vs)
                lows.append((l, ls))
                highs.append((h, hs))
        lo, lo_s = _hull(lows, lower=True)
        hi, hi_s = _hull(highs, lower=False)
        x = ("var", var)
        parts = []
        if lo is not None and hi is not None and lo == hi:
            parts = [("rel", "=", x, ("lit", lo))]
        else:
            if lo is not None:
                parts.append(("rel", ">" if lo_s else ">=", x, ("lit", lo)))
            if hi is not None:
                parts.append(("rel", "<" if hi_s else "<=", x, ("lit", hi)))
        if not parts:
            out = ("free", var)
        else:
            out = parts[0] if len(parts) == 1 else ("and", tuple(parts))
        # certificates: each bound entailed; each non-strict bound attained
        entailed, attained = [], []
        for part in parts:
            e_ok, e_got = _entails_raw(ps, part, vs)
            if not e_ok:
                raise AssertionError("a projected bound is not entailed")
            entailed.append({"bound": _enc(part), "certificates": e_got})
            if part[1] in ("=", "<=", ">="):
                pin = ("rel", "=", x, part[3])
                a_ok, a_got = _consistent(ps + [pin], vs)
                if not a_ok:
                    raise AssertionError("a non-strict bound is not attained")
                attained.append({"bound": _enc(part),
                                 "witness": _enc_point(a_got)})
        cert = {"kind": "bounds", "premises": [_enc(s) for s in ps],
                "var": var, "answer": _enc(out), "entailed": entailed,
                "attained": attained}
        return Answer(op, "BOUNDED" if parts else "FREE", realise(out),
                      [realise(s) for s in ps] + [realise(out)],
                      [_math(s) for s in ps] + [_math(out)], cert)
    except ReverseRefusal as exc:
        return _refused(op, exc)


# -- paraphrase ---------------------------------------------------------------

def _mirror(t, deep: bool):
    k = t[0]
    if k in ("add", "mul", "min", "max"):
        a, b = t[1], t[2]
        if deep:
            a, b = _mirror(a, True), _mirror(b, True)
        return (k, b, a)
    if not deep or k in ("lit", "var", "mask"):
        return t
    if k == "pow":
        return ("pow", _mirror(t[1], True), t[2])
    if k in _UN_WORDS:
        return (k, _mirror(t[1], True))
    return (k, _mirror(t[1], True), _mirror(t[2], True))


def _canon_or_self(t):
    try:
        return canonical_term(poly_of(t))
    except ReverseRefusal:
        return t


def _paraphrases(obj) -> List:
    out = []
    if not _is_statement(obj):
        out.append(_canon_or_self(obj))
        out.append(_mirror(obj, False))
        out.append(_mirror(obj, True))
        return out
    clauses = _clauses(obj)
    flat = all(len(c) == 1 for c in clauses)

    def conv(r):
        if r[1] not in _CONVERSE:
            return r
        return ("rel", _CONVERSE[r[1]], _mirror(r[3], True),
                _mirror(r[2], True))

    def canon(r):
        if r[1] not in _HOLDS:
            return r
        return ("rel", r[1], _canon_or_self(r[2]), _canon_or_self(r[3]))
    out.append(_from_clauses([[canon(r) for r in c] for c in clauses]))
    out.append(_from_clauses(list(reversed(clauses))))
    out.append(_from_clauses([[conv(r) for r in reversed(c)]
                              for c in reversed(clauses)]))
    if flat:
        try:
            out.append(_from_clauses([[("rel", c[0][1], canonical_term(
                _padd(poly_of(c[0][2]), poly_of(c[0][3]), -1)),
                ("lit", Fraction(0)))] for c in clauses]))
        except ReverseRefusal:
            pass
    if flat and len(clauses) == 1:
        r = clauses[0][0]
        for v in _variables(r):
            got = solve(v, realise(r))
            if got.answered:
                out.append(read(got.sentence))
                break
    return out


def paraphrase(text: str) -> Answer:
    op = "paraphrase"
    try:
        obj, _ = parse_any(text)
        if obj[0] == "prog":
            raise _nf("paraphrase takes a term or a statement")
        original = realise(obj)
        seen, sentences, certs = {original}, [], []
        for cand in _paraphrases(obj):
            s = realise(cand)
            if s in seen:
                continue
            back = read(s)
            check = equivalent(original, s)
            if check.verdict != "SAME":
                if check.answered:
                    raise AssertionError(f"paraphrase not equivalent: {s!r}")
                continue
            seen.add(s)
            sentences.append(s)
            certs.append({"sentence": s, "structure": _enc(back),
                          "certificate": check.certificate})
        return Answer(op, "PARAPHRASED", sentences[0] if sentences else "",
                      [original] + sentences, [_math(obj)],
                      {"kind": "paraphrase", "original": _enc(obj),
                       "paraphrases": certs})
    except ReverseRefusal as exc:
        return _refused(op, exc)


# ===========================================================================
# 8.  JSON ENCODING FOR COLUMN 3
# ===========================================================================

def _q(x) -> str:
    f = Fraction(x)
    return f"{f.numerator}/{f.denominator}"


def _enc(obj):
    if isinstance(obj, Fraction):
        return _q(obj)
    if isinstance(obj, (tuple, list)):
        return [_enc(x) for x in obj]
    return obj


def _enc_point(p: Dict[str, Fraction]) -> Dict[str, str]:
    return {v: _q(c) for v, c in sorted(p.items())}


def _enc_certs(certs) -> List:
    return [{"rows": [[op, _enc(a), _enc(b)] for op, a, b in c["rows"]],
             "multipliers": [_q(m) for m in c["multipliers"]]}
            for c in certs]


def _dec(x):
    """Inverse of :func:`_enc` for terms and statements."""
    if isinstance(x, list):
        if x and x[0] == "lit":
            n, d = x[1].split("/")
            return ("lit", Fraction(int(n), int(d)))
        if x and x[0] == "mask":
            return ("mask", tuple(x[1]))
        if x and x[0] in ("and", "or"):
            return (x[0], tuple(_dec(r) for r in x[1]))
        if x and x[0] == "prog":
            return ("prog", tuple((n, _dec(t)) for n, t in x[1]), _dec(x[2]))
        return tuple(_dec(y) if isinstance(y, list) else y for y in x)
    return x


# ===========================================================================
# 9.  THE QUESTION SURFACE
# ===========================================================================

#: The operations, by the prefix that asks for them.  ``relay:`` is read
#: here and answered by :mod:`glm_universal.runtime.reverse_relay`, which may
#: call the planner (the reasoning layer does not).
OPERATIONS: Tuple[str, ...] = ("say:", "equivalent:", "paraphrase:",
                               "negate:", "solve for", "entails:",
                               "bounds of", "relay:",
                               "entails over the integers:",
                               "bounds over the integers of")


def reads(text: str) -> bool:
    """Whether the reverse surface reads ``text``: it starts with an
    operation prefix (every prefix carries a colon, which no dialect program
    and no planner question begins with)."""
    t = text.strip().lower()
    if t.startswith("entails over ") or t.startswith("bounds over "):
        from .reverse_tct_int import reads_int
        return reads_int(text)
    if t.startswith("solve for ") or t.startswith("bounds of "):
        head = t.split(":", 1)[0].split()
        return ":" in t and len(head) == 3
    return any(t.startswith(p) for p in OPERATIONS if p.endswith(":"))


def answer(text: str) -> Answer:
    """Answer one question of the reverse surface (``relay:`` excepted: it
    is the runtime's)."""
    t = text.strip()
    low = t.lower()
    if low.startswith("entails over ") or low.startswith("bounds over "):
        from .reverse_tct_int import answer_int, reads_int
        if reads_int(t):
            return answer_int(t)
        return _refused("reverse", ReverseRefusal(
            "UNREADABLE", "entails over the integers: PREMISES ; CONCLUSION, "
            "or bounds over the integers of x: PREMISES"))
    if low.startswith("say:"):
        return say(t[4:].strip())
    if low.startswith("equivalent:"):
        body = t[len("equivalent:"):]
        if ";" not in body:
            return _refused("equivalent", ReverseRefusal(
                "UNREADABLE", "equivalent: FIRST ; SECOND"))
        a, b = body.split(";", 1)
        return equivalent(a.strip(), b.strip())
    if low.startswith("paraphrase:"):
        return paraphrase(t[len("paraphrase:"):].strip())
    if low.startswith("negate:"):
        return negate(t[len("negate:"):].strip())
    if low.startswith("solve for ") or low.startswith("bounds of "):
        head, body = t.split(":", 1)
        var = head.split()[2]
        if low.startswith("solve for "):
            return solve(var, body.strip())
        return bounds(var, [q for x in body.split(";")
                            for q in _premise_list(x)])
    if low.startswith("entails:"):
        body = t[len("entails:"):]
        if ";" not in body:
            return _refused("entails", ReverseRefusal(
                "UNREADABLE", "entails: PREMISES ; CONCLUSION"))
        parts = [x.strip() for x in body.split(";")]
        ps = [q for x in parts[:-1] for q in _premise_list(x)]
        return entails(ps, parts[-1])
    if low.startswith("relay:"):
        return _refused("relay", ReverseRefusal(
            "UNREADABLE", "relay: is answered by the runtime (it calls the "
            "planner); ask it through GLM.py --ask or the router"))
    return _refused("reverse", ReverseRefusal("UNREADABLE",
                                              "no operation prefix"))


def _premise_list(text: str) -> List[str]:
    """One ``;``-separated part of a premise list, split further at
    ``&&``; a single sentence may itself be a conjunction (``, and`` in the
    grammar, ``and`` in the dialect)."""
    text = text.strip()
    if "&&" in text:
        return [p.strip() for p in text.split("&&") if p.strip()]
    return [text]
