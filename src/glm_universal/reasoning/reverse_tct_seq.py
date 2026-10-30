"""``glm_universal.reasoning.reverse_tct_seq`` -- the third sort of Reverse TCT.

Phase 94 (``studies/THIRD_SORT_STUDY.md``).  Beside numbers and Golay masks,
the reverse grammar now names **strings, tuples and ranges**: finite
sequences, each literal spelled with its count first so that its extent is
fixed before its items are read (the discipline that kept the Phase 68 mask
literals uniquely readable; ``RequestProject/GLM/ThirdSort.lean`` proves the
general fact).

The sort is asked for by ``say:`` only, of closed terms, closed statements
and ``let`` programs.  :func:`reverse_tct.say` asks the earlier grammar first
and calls :func:`say_third_sort` only when that refuses ``NOT_IN_FRAGMENT`` or
``UNREADABLE``; when the third sort cannot read the text either, the earlier
refusal stands -- so no earlier answer can change.

The grammar here is a superset of the earlier one: every earlier term is
realised and read exactly as before (the reader is a subclass whose new
heads are tried first, and every earlier head falls through to the earlier
reader), and the new heads are disjoint from the old.

Exact throughout: code points, ``Fraction`` and ``int``; no float, no clock,
no randomness.  The column-3 script is :func:`render_script`; it re-reads
every column-1 sentence with :func:`read` and re-derives the value with an
evaluator of its own.
"""

from __future__ import annotations

import ast
import json
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import reverse_tct as rt
from .reverse_tct import (Answer, ReverseRefusal, _BIN_SORT, _BIN_WORDS,
                          _UN_SORT, _UN_WORDS, _join, _lit_words, _mask_words,
                          _NEGATION, _RELATIONS, _tokens, number_words)

__all__ = ["SEQ_WORDS", "SEQ_RESERVED", "realise_term", "realise", "read",
           "from_source", "parse_any", "evaluate", "holds", "say_third_sort",
           "render_script", "mutated_script", "char_words", "value_term",
           "value_of", "clamp_indices",
           "battery_terms", "CODE_POINT_LIMIT"]

#: The largest code point (CPython's ``chr`` limit).
CODE_POINT_LIMIT = 0x10FFFF
#: Longest sequence the evaluator builds (a guard, not a property of the
#: grammar).
LENGTH_LIMIT = 4096

#: The words the third sort adds; none may name a variable.
SEQ_WORDS = frozenset({
    "string", "characters", "character", "tuple", "entries", "entry",
    "range", "from", "to", "by", "concatenation", "repetition", "times",
    "slice", "default", "item", "length", "total", "code", "point",
    "least", "greatest", "capital", "small", "digit", "space", "entries"})
SEQ_RESERVED = rt.RESERVED | SEQ_WORDS

_LETTERS = "abcdefghijklmnopqrstuvwxyz"


# ===========================================================================
# 1.  THE REALISER (column 2 -> column 1)
# ===========================================================================

def char_words(cp: int) -> List[str]:
    """The canonical spelling of one code point."""
    if 65 <= cp <= 90:
        return ["capital", chr(cp + 32)]
    if 97 <= cp <= 122:
        return ["small", chr(cp)]
    if 48 <= cp <= 57:
        return ["digit"] + number_words(cp - 48)
    if cp == 32:
        return ["space"]
    return ["code", "point"] + number_words(cp)


def _named(cp: int) -> bool:
    return 65 <= cp <= 90 or 97 <= cp <= 122 or 48 <= cp <= 57 or cp == 32


def _count_first(head: str, singular: str, plural: str,
                 items: Sequence[List[str]]) -> List[str]:
    out = ["the", head, "of"] + number_words(len(items)) + [
        singular if len(items) == 1 else plural]
    for i, ws in enumerate(items):
        if i:
            out.append(",")
        out += ws
    return out


def realise_term(t) -> List[str]:
    """Column 1 of one term (any sort), as a token list."""
    k = t[0]
    if k == "str":
        if not t[1]:
            return ["the", "empty", "string"]
        return _count_first("string", "character", "characters",
                            [char_words(c) for c in t[1]])
    if k == "tup":
        if not t[1]:
            return ["the", "empty", "tuple"]
        return _count_first("tuple", "entry", "entries",
                            [realise_term(e) for e in t[1]])
    if k == "range":
        return (["the", "range", "from"] + realise_term(t[1]) + ["to"]
                + realise_term(t[2]) + ["by"] + realise_term(t[3]))
    if k == "concat":
        return (["the", "concatenation", "of"] + realise_term(t[1]) + ["and"]
                + realise_term(t[2]))
    if k == "repeat":
        return (["the", "repetition", "of"] + realise_term(t[1]) + ["times"]
                + realise_term(t[2]))
    if k == "slice":
        def bound(b):
            return ["the", "default"] if b is None else realise_term(b)
        return (["the", "slice", "of"] + realise_term(t[1]) + ["from"]
                + bound(t[2]) + ["to"] + bound(t[3]) + ["by"]
                + realise_term(t[4]))
    if k == "item":
        return (["the", "item", "of"] + realise_term(t[1]) + ["at"]
                + realise_term(t[2]))
    if k in _SEQ_UNARY:
        return ["the", *_SEQ_UNARY[k], "of"] + realise_term(t[1])
    # -- the earlier grammar, recursing through this realiser -------------
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


#: One-argument heads of the third sort.
_SEQ_UNARY: Dict[str, Tuple[str, ...]] = {
    "chr": ("character",), "entries": ("entries",), "length": ("length",),
    "total": ("total",), "ord": ("code", "point"),
    "least": ("least", "entry"), "greatest": ("greatest", "entry"),
}


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
    raise ValueError(f"not a statement: {s!r}")


def realise(obj) -> str:
    """Column 1 of a term, a statement or a program, as one string."""
    k = obj[0]
    if k in ("rel", "and", "or"):
        return _join(_realise_statement(obj))
    if k == "prog":
        toks: List[str] = []
        for name, term in obj[1]:
            toks += ["let", name, "be"] + realise_term(term) + ["."]
        toks += ["the", "result", "is"] + realise_term(obj[2]) + ["."]
        return _join(toks)
    return _join(realise_term(obj))


# ===========================================================================
# 2.  THE READER (column 1 -> column 2)
# ===========================================================================

def _unreadable(msg: str) -> ReverseRefusal:
    return ReverseRefusal("UNREADABLE", msg)


class _SeqReader(rt._Reader):
    """The earlier reader with the third sort's heads tried first."""

    def count_first(self, head: str, singular: str, plural: str, item):
        self.expect("the", head, "of")
        k = self.natural()
        if k == 0:
            raise _unreadable(f"an empty {head} is spelled 'the empty {head}'")
        self.expect(singular if k == 1 else plural)
        out = []
        for j in range(k):
            if j:
                self.expect(",")
            out.append(item())
        return tuple(out)

    def character(self) -> int:
        t = self.peek()
        if t in ("capital", "small"):
            self.i += 1
            x = self.peek()
            if x is None or len(x) != 1 or x not in _LETTERS:
                raise _unreadable(f"'{t}' is followed by one letter a to z")
            self.i += 1
            return ord(x) - (32 if t == "capital" else 0)
        if t == "digit":
            self.i += 1
            n = self.natural()
            if n > 9:
                raise _unreadable("a digit is zero to nine")
            return 48 + n
        if t == "space":
            self.i += 1
            return 32
        if t == "code":
            self.expect("code", "point")
            n = self.natural()
            if n > CODE_POINT_LIMIT:
                raise _unreadable("no code point lies above 1114111")
            if _named(n):
                raise _unreadable("a letter, a digit or the space is spelled "
                                  "by its name, not by its code point")
            return n
        raise _unreadable(f"a character was expected at {t!r}")

    def bound(self):
        if self.ahead(("the", "default")):
            self.expect("the", "default")
            return None
        return self.term()

    def term(self):
        t = self.peek()
        if t == "the":
            h = self.peek(1)
            if h == "empty" and self.peek(2) in ("string", "tuple"):
                kind = self.peek(2)
                self.expect("the", "empty", kind)
                return ("str" if kind == "string" else "tup", ())
            if h == "string" and self.peek(2) == "of":
                return ("str", self.count_first("string", "character",
                                                "characters", self.character))
            if h == "tuple" and self.peek(2) == "of":
                return ("tup", self.count_first("tuple", "entry", "entries",
                                                self.term))
            if h == "range" and self.peek(2) == "from":
                self.expect("the", "range", "from")
                a = self.term()
                self.expect("to")
                b = self.term()
                self.expect("by")
                return ("range", a, b, self.term())
            if self.ahead(("the", "concatenation", "of")):
                self.expect("the", "concatenation", "of")
                a = self.term()
                self.expect("and")
                return ("concat", a, self.term())
            if self.ahead(("the", "repetition", "of")):
                self.expect("the", "repetition", "of")
                a = self.term()
                self.expect("times")
                return ("repeat", a, self.term())
            if self.ahead(("the", "slice", "of")):
                self.expect("the", "slice", "of")
                s = self.term()
                self.expect("from")
                a = self.bound()
                self.expect("to")
                b = self.bound()
                self.expect("by")
                if self.ahead(("the", "default")):
                    raise _unreadable("a slice's step is always spelled; an "
                                      "omitted step is one")
                return ("slice", s, a, b, self.term())
            if self.ahead(("the", "item", "of")):
                self.expect("the", "item", "of")
                s = self.term()
                self.expect("at")
                return ("item", s, self.term())
            for k, ws in sorted(_SEQ_UNARY.items(), key=lambda kv: -len(kv[1])):
                if self.ahead(("the",) + ws + ("of",)):
                    self.expect("the", *ws, "of")
                    return (k, self.term())
        if (t is not None and t.isidentifier() and t in SEQ_WORDS
                and t not in rt.RESERVED):
            raise _unreadable(f"{t!r} is a grammar word and names no variable")
        return super().term()


def read(text: str):
    """Column 2 of a sentence of the widened grammar: a program, a statement
    or a term (no sort check: sorts are decided by :func:`evaluate`)."""
    toks = _tokens(text)
    if not toks:
        raise _unreadable("the empty sentence")
    last: Optional[ReverseRefusal] = None
    for kind in ("program", "statement", "term"):
        if kind == "program" and not (toks[0] == "let" or toks[:3] == [
                "the", "result", "is"]):
            continue
        r = _SeqReader(toks)
        try:
            obj = getattr(r, kind)()
            r.done()
        except ReverseRefusal as exc:
            last = exc
            continue
        if obj[0] == "free":
            raise _unreadable("'nothing bounds' is not a sentence of the "
                              "third sort")
        return obj
    raise last if last is not None else _unreadable(text)


# ===========================================================================
# 3.  COLUMN 3 IN -- THE DIALECT'S SYNTAX
# ===========================================================================

def _nf(msg: str) -> ReverseRefusal:
    return ReverseRefusal("NOT_IN_FRAGMENT", msg)


def _mismatch(msg: str) -> ReverseRefusal:
    return ReverseRefusal("SORT_MISMATCH", msg)


def _vsort(v) -> str:
    if isinstance(v, frozenset):
        return "m"
    if isinstance(v, str):
        return "s"
    if isinstance(v, tuple):
        return "t"
    if isinstance(v, range):
        return "r"
    return "n"


class _Source:
    """Reads dialect source into terms, tracking the values of ``let``-bound
    names so that a mask, a number and a sequence are told apart."""

    def __init__(self) -> None:
        self.env: Dict[str, object] = {}

    def sort(self, t) -> str:
        try:
            return _vsort(evaluate(t, self.env))
        except ReverseRefusal:
            return "n"

    def term(self, node):
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, bool):
                raise _nf("booleans have no sentence in the grammar")
            if isinstance(v, int):
                return ("lit", Fraction(v))
            if isinstance(v, str):
                return ("str", tuple(ord(c) for c in v))
            raise _nf(f"the literal {v!r} is not an exact rational, a string "
                      "or a tuple")
        if isinstance(node, ast.Name):
            if node.id in SEQ_RESERVED or not node.id.isidentifier():
                raise _nf(f"{node.id!r} is a grammar word and cannot name a "
                          "variable")
            return ("var", node.id)
        if isinstance(node, ast.Tuple):
            return ("tup", tuple(self.term(e) for e in node.elts))
        if isinstance(node, ast.Subscript):
            s = self.term(node.value)
            sl = node.slice
            if isinstance(sl, ast.Slice):
                a = None if sl.lower is None else self.term(sl.lower)
                b = None if sl.upper is None else self.term(sl.upper)
                c = ("lit", Fraction(1)) if sl.step is None else self.term(
                    sl.step)
                return ("slice", s, a, b, c)
            return ("item", s, self.term(sl))
        if isinstance(node, ast.Call):
            return self.call(node)
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                v = rt._int_const(node)
                if v is not None:
                    return ("lit", Fraction(v))
                return ("neg", self.term(node.operand))
            if isinstance(node.op, ast.Invert):
                return ("compl", self.term(node.operand))
            raise _nf(f"the unary operator {type(node.op).__name__}")
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Pow):
                n = rt._int_const(node.right)
                if n is None:
                    raise _nf("a power's exponent must be a literal integer")
                return ("pow", self.term(node.left), n)
            a, b = self.term(node.left), self.term(node.right)
            sa, sb = self.sort(a), self.sort(b)
            seq = ("s", "t", "r")
            if isinstance(node.op, ast.Add) and (sa in seq or sb in seq):
                return ("concat", a, b)
            if isinstance(node.op, ast.Mult) and (sa in seq or sb in seq):
                return ("repeat", a, b) if sa in seq else ("repeat", b, a)
            for cls, (num, mask) in rt._BITS.items():
                if isinstance(node.op, cls):
                    if (sa == "m") != (sb == "m"):
                        raise _mismatch("a mask is not a number")
                    return (mask if sa == "m" else num, a, b)
            for cls, name in rt._ARITH.items():
                if isinstance(node.op, cls):
                    if name == "sub" and sa == "m" and sb == "m":
                        return ("setdiff", a, b)
                    return (name, a, b)
            raise _nf(f"the operator {type(node.op).__name__}")
        raise _nf(f"the construct {type(node).__name__}")

    def call(self, node):
        f = node.func.id if isinstance(node.func, ast.Name) else None
        if node.keywords:
            raise _nf(f"keyword arguments to {f}")
        args = node.args
        if f == "Fraction" and 1 <= len(args) <= 2:
            ints = [rt._int_const(a) for a in args]
            if all(v is not None for v in ints):
                if len(ints) == 2 and ints[1] == 0:
                    raise ReverseRefusal("DIVISION_BY_ZERO",
                                         "Fraction with denominator zero")
                return ("lit", Fraction(*ints))
            raise _nf("a call other than Fraction(int[, int])")
        if f == "frozenset":
            return rt._mask_of(node)
        if f == "abs" and len(args) == 1:
            return ("abs", self.term(args[0]))
        if f == "hamming" and len(args) == 2:
            return ("dist", self.term(args[0]), self.term(args[1]))
        if f == "len" and len(args) == 1:
            s = self.term(args[0])
            return ("size", s) if self.sort(s) == "m" else ("length", s)
        if f in ("ord", "chr") and len(args) == 1:
            return (f, self.term(args[0]))
        if f == "tuple" and len(args) == 1:
            return ("entries", self.term(args[0]))
        if f == "tuple" and not args:
            return ("tup", ())
        if f == "range" and 1 <= len(args) <= 3:
            ts = [self.term(a) for a in args]
            if len(ts) == 1:
                return ("range", ("lit", Fraction(0)), ts[0],
                        ("lit", Fraction(1)))
            if len(ts) == 2:
                return ("range", ts[0], ts[1], ("lit", Fraction(1)))
            return ("range", ts[0], ts[1], ts[2])
        if f in ("min", "max", "sum"):
            if len(args) == 1 and isinstance(args[0], ast.Tuple):
                items = [self.term(a) for a in args[0].elts]
                if not items:
                    if f == "sum":
                        return ("lit", Fraction(0))
                    raise _nf(f"{f} of nothing")
                if len(items) == 1:
                    return items[0]
                return rt._nest({"min": "min", "max": "max", "sum": "add"}[f],
                                items, right=(f != "sum"))
            if len(args) == 1:
                kind = {"min": "least", "max": "greatest", "sum": "total"}[f]
                return (kind, self.term(args[0]))
            if f != "sum" and len(args) >= 2:
                return rt._nest(f, [self.term(a) for a in args], right=True)
            raise _nf(f"{f} of a sequence or of two or more terms")
        if f == "pow" and len(args) in (2, 3):
            n = rt._int_const(args[1])
            if n is None:
                raise _nf("a power's exponent must be a literal integer")
            base = ("pow", self.term(args[0]), n)
            if len(args) == 2:
                return base
            if n < 0:
                raise _nf("pow(a, n, m) with a negative n")
            return ("mod", base, self.term(args[2]))
        raise _nf(f"the call {f or type(node.func).__name__}(...)")

    def statement(self, node, positive: bool = True):
        if isinstance(node, ast.Compare):
            rels = []
            left = node.left
            for op, right in zip(node.ops, node.comparators):
                sym = next((s for c, s in rt._CMP.items()
                            if isinstance(op, c)), None)
                if sym is None:
                    raise _nf(f"the comparison {type(op).__name__}")
                a, b = self.term(left), self.term(right)
                if sym == "<=" and self.sort(a) == "m" and self.sort(b) == "m":
                    sym = "sub"
                elif (sym in ("<", ">", ">=")
                      and "m" in (self.sort(a), self.sort(b))):
                    raise _nf("of the orders on masks only <= (contained in) "
                              "has a sentence")
                rels.append(("rel", sym, a, b))
                left = right
            if positive:
                return [[r] for r in rels]
            return [[rt._neg_rel(r) for r in rels]]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            got = self.statement(node.operand, not positive)
            if got is None:
                raise _nf("'not' applies to a statement, not a term")
            return got
        if isinstance(node, ast.BoolOp):
            parts = []
            for v in node.values:
                got = self.statement(v, positive)
                if got is None:
                    raise _nf("'and' and 'or' join statements, not terms")
                parts.append(got)
            if isinstance(node.op, ast.And) == positive:
                return [c for p in parts for c in p]
            return rt._distribute(parts)
        return None

    def expr(self, node):
        cnf = self.statement(node)
        if cnf is None:
            return self.term(node)
        return rt._from_clauses(cnf)


def from_source(source: str):
    """Column 2 of a dialect program, expression or comparison, with the
    third sort."""
    try:
        tree = ast.parse(source.strip())
    except SyntaxError as exc:
        raise _nf(f"not Python: {exc.msg}") from None
    body = tree.body
    if not body:
        raise _nf("the empty program")
    reader = _Source()
    if len(body) == 1 and isinstance(body[0], ast.Expr):
        return reader.expr(body[0].value)
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
            if any(rt._loads(v) & names for v in st.value.elts):
                raise _nf("a simultaneous assignment that reads its own "
                          "targets has no sequential reading")
            pairs = list(zip(target.elts, st.value.elts))
        else:
            raise _nf("a program is assignments to names, then a result")
        for name_node, value in pairs:
            name = name_node.id
            if name in SEQ_RESERVED:
                raise _nf(f"{name!r} is a grammar word")
            term = reader.term(value)
            binds.append((name, term))
            try:
                reader.env[name] = evaluate(term, reader.env)
            except ReverseRefusal:
                reader.env.pop(name, None)
    last = body[-1]
    if not isinstance(last, ast.Expr):
        raise _nf("a program ends with its result expression")
    return ("prog", tuple(binds), reader.term(last.value))


def parse_any(text: str):
    """Column 2 of ``text``: a sentence of the widened grammar if it is one,
    else dialect source.  Returns ``(object, 'language'|'source')``."""
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
# 4.  COLUMN 2 -- EVALUATION
# ===========================================================================

def _int(v, what: str) -> int:
    if isinstance(v, Fraction) and v.denominator == 1:
        return v.numerator
    if isinstance(v, Fraction):
        raise ReverseRefusal("NOT_INTEGER", f"{what} takes integers; {v} is "
                             "not one")
    raise _mismatch(f"{what} takes a number")


def _seq(v, what: str, kinds=("s", "t", "r")):
    if _vsort(v) not in kinds:
        raise _mismatch(f"{what} takes a "
                        + " or a ".join({"s": "string", "t": "tuple",
                                         "r": "range"}[k] for k in kinds))
    return v


def clamp_indices(n: int, start: Optional[int], stop: Optional[int],
                  step: int) -> List[int]:
    """CPython's slice reading of a sequence of length ``n``, written out:
    the default ends, negative indices from the end, clamping, then the
    index map ``i -> start + i*step`` while it stays short of ``stop``."""
    if step == 0:
        raise ReverseRefusal("ZERO_STEP", "a slice by step zero")
    if step > 0:
        lo, hi = 0, n
    else:
        lo, hi = -1, n - 1
    if start is None:
        a = lo if step > 0 else hi
    else:
        a = start + n if start < 0 else start
        a = min(max(a, lo), hi)
    if stop is None:
        b = hi if step > 0 else lo
    else:
        b = stop + n if stop < 0 else stop
        b = min(max(b, lo), hi)
    out = []
    i = a
    while (i < b) if step > 0 else (i > b):
        out.append(i)
        i += step
    return out


def _equal(a, b) -> bool:
    sa, sb = _vsort(a), _vsort(b)
    if sa != sb:
        return False
    if sa == "t":
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    if sa == "r":
        return list(a) == list(b) if len(a) == len(b) else False
    return a == b


def _order(a, b) -> int:
    """CPython's order on two values of one sort: numbers by sign, strings by
    code points, tuples lexicographically; anything else is refused."""
    sa, sb = _vsort(a), _vsort(b)
    if sa == sb == "n":
        return (a > b) - (a < b)
    if sa == sb == "s":
        for x, y in zip(a, b):
            if ord(x) != ord(y):
                return 1 if ord(x) > ord(y) else -1
        return (len(a) > len(b)) - (len(a) < len(b))
    if sa == sb == "t":
        for x, y in zip(a, b):
            if not _equal(x, y):
                return _order(x, y)
        return (len(a) > len(b)) - (len(a) < len(b))
    raise _mismatch("an order relates two numbers, two strings or two "
                    "tuples")


def _guard(n: int) -> None:
    if n > LENGTH_LIMIT:
        raise _nf(f"a sequence longer than {LENGTH_LIMIT}")


def evaluate(t, env: Dict[str, object]):
    """The exact value of a term: a ``Fraction``, a ``frozenset`` (a mask), a
    ``str``, a ``tuple`` or a ``range``."""
    k = t[0]
    if k == "str":
        return "".join(chr(c) for c in t[1])
    if k == "tup":
        return tuple(evaluate(e, env) for e in t[1])
    if k == "var":
        if t[1] not in env:
            raise _nf(f"{t[1]} is unbound; a term of the third sort has no "
                      "free variables")
        return env[t[1]]
    if k == "range":
        a, b, c = (_int(evaluate(x, env), "a range") for x in t[1:])
        if c == 0:
            raise ReverseRefusal("ZERO_STEP", "a range by step zero")
        return range(a, b, c)
    if k == "concat":
        a, b = evaluate(t[1], env), evaluate(t[2], env)
        sa, sb = _vsort(a), _vsort(b)
        if sa != sb or sa not in ("s", "t"):
            raise _mismatch("a concatenation joins two strings or two tuples")
        _guard(len(a) + len(b))
        return a + b
    if k == "repeat":
        s = _seq(evaluate(t[1], env), "a repetition", ("s", "t"))
        n = _int(evaluate(t[2], env), "a repetition's count")
        _guard(max(n, 0) * len(s))
        return s * max(n, 0)
    if k == "slice":
        s = _seq(evaluate(t[1], env), "a slice")
        a = None if t[2] is None else _int(evaluate(t[2], env), "a slice")
        b = None if t[3] is None else _int(evaluate(t[3], env), "a slice")
        c = _int(evaluate(t[4], env), "a slice")
        idx = clamp_indices(len(s), a, b, c)
        if isinstance(s, range):
            return s[slice(a, b, c)]
        if isinstance(s, str):
            return "".join(s[i] for i in idx)
        return tuple(s[i] for i in idx)
    if k == "item":
        s = _seq(evaluate(t[1], env), "an item")
        i = _int(evaluate(t[2], env), "an index")
        j = i + len(s) if i < 0 else i
        if not 0 <= j < len(s):
            raise ReverseRefusal("INDEX_OUT_OF_RANGE",
                                 f"index {i} of a sequence of {len(s)}")
        v = s[j]
        return Fraction(v) if isinstance(s, range) else v
    if k == "chr":
        n = _int(evaluate(t[1], env), "a character")
        if not 0 <= n <= CODE_POINT_LIMIT:
            raise ReverseRefusal("NOT_A_CHARACTER", f"no character has code "
                                 f"point {n}")
        return chr(n)
    if k == "ord":
        s = _seq(evaluate(t[1], env), "a code point", ("s",))
        if len(s) != 1:
            raise ReverseRefusal("NOT_A_CHARACTER", f"a code point is read "
                                 f"off one character, not {len(s)}")
        return Fraction(ord(s))
    if k == "entries":
        s = _seq(evaluate(t[1], env), "the entries")
        _guard(len(s))
        return tuple(Fraction(x) for x in s) if isinstance(s, range) \
            else tuple(s)
    if k == "length":
        return Fraction(len(_seq(evaluate(t[1], env), "a length")))
    if k == "total":
        s = _seq(evaluate(t[1], env), "a total", ("t", "r"))
        if isinstance(s, range):
            n = len(s)
            return Fraction(n * (2 * s.start + (n - 1) * s.step), 2) \
                if n else Fraction(0)
        out = Fraction(0)
        for x in s:
            if _vsort(x) != "n":
                raise _mismatch("a total adds numbers")
            out += x
        return out
    if k in ("least", "greatest"):
        s = _seq(evaluate(t[1], env), f"the {k} entry")
        if len(s) == 0:
            raise ReverseRefusal("EMPTY_SEQUENCE", f"the {k} entry of an "
                                 "empty sequence")
        items = list(s)
        best = items[0]
        for x in items[1:]:
            o = _order(x, best)
            if (o < 0) if k == "least" else (o > 0):
                best = x
        return Fraction(best) if isinstance(s, range) else best
    # -- the earlier operators, over values of the earlier sorts ----------
    if k in ("lit", "mask"):
        return rt.evaluate(t, {})
    if k == "pow":
        v = evaluate(t[1], env)
        if _vsort(v) != "n":
            raise _mismatch("only a number has a power")
        return rt.evaluate(("pow", value_term(v), t[2]), {})
    if k in _UN_SORT:
        want, _ = _UN_SORT[k]
        v = evaluate(t[1], env)
        if _vsort(v) != want:
            raise _mismatch(f"{' '.join(_UN_WORDS[k])} takes "
                            f"{'a mask' if want == 'm' else 'a number'}")
        return rt.evaluate((k, value_term(v)), {})
    if k in _BIN_SORT:
        wa, wb, _ = _BIN_SORT[k]
        a, b = evaluate(t[1], env), evaluate(t[2], env)
        if _vsort(a) != wa or _vsort(b) != wb:
            raise _mismatch(f"{' '.join(_BIN_WORDS[k])} takes "
                            f"{'masks' if wa == 'm' else 'numbers'}")
        return rt.evaluate((k, value_term(a), value_term(b)), {})
    raise ValueError(f"not a term: {t!r}")


def value_term(v):
    """A value as a closed literal term of its sort."""
    if isinstance(v, bool):
        raise _nf("booleans have no sentence in the grammar")
    if isinstance(v, frozenset):
        return ("mask", tuple(sorted(v)))
    if isinstance(v, str):
        return ("str", tuple(ord(c) for c in v))
    if isinstance(v, tuple):
        return ("tup", tuple(value_term(x) for x in v))
    if isinstance(v, range):
        return ("range", ("lit", Fraction(v.start)), ("lit", Fraction(v.stop)),
                ("lit", Fraction(v.step)))
    return ("lit", Fraction(v))


def _contains(container, item) -> bool:
    sc = _vsort(container)
    if sc == "m":
        return rt.holds(("rel", "in", value_term(item),
                         value_term(container)), {}) if _vsort(item) == "n" \
            else False
    if sc == "s":
        if _vsort(item) != "s":
            raise _mismatch("'in' a string takes a string")
        n, m = len(container), len(item)
        return any(all(ord(container[i + j]) == ord(item[j])
                       for j in range(m)) for i in range(n - m + 1))
    if sc == "t":
        return any(_equal(item, x) for x in container)
    if sc == "r":
        if _vsort(item) != "n" or item.denominator != 1:
            return False
        x, r = item.numerator, container
        if r.step > 0 and not r.start <= x < r.stop:
            return False
        if r.step < 0 and not r.stop < x <= r.start:
            return False
        return (x - r.start) % r.step == 0
    raise _mismatch("'in' takes a mask, a string, a tuple or a range")


def holds(s, env) -> bool:
    if s[0] == "and":
        return all(holds(r, env) for r in s[1])
    if s[0] == "or":
        return any(holds(r, env) for r in s[1])
    a, b = evaluate(s[2], env), evaluate(s[3], env)
    op = s[1]
    if op in ("in", "notin"):
        return _contains(b, a) == (op == "in")
    if op in ("sub", "notsub"):
        if _vsort(a) != "m" or _vsort(b) != "m":
            raise _mismatch("contained in relates two masks")
        return (a <= b) == (op == "sub")
    if op in ("=", "!="):
        if _vsort(a) != _vsort(b):
            raise _mismatch("equality relates two terms of one sort")
        return _equal(a, b) == (op == "=")
    o = _order(a, b)
    return {"<": o < 0, "<=": o <= 0, ">": o > 0, ">=": o >= 0}[op]


# ===========================================================================
# 5.  SAY -- COLUMN 1 GENERATED, WITH THE VALUE
# ===========================================================================

_MATH_UN = {"chr": "chr", "entries": "tuple", "length": "len",
            "total": "Σ", "ord": "ord", "least": "min", "greatest": "max"}


def _math(obj) -> str:
    """Column 2's rendering, exact and fully bracketed."""
    k = obj[0]
    if k == "str":
        return "⟨" + " ".join(f"U+{c:04X}" for c in obj[1]) + "⟩"
    if k == "tup":
        return "(" + ", ".join(_math(e) for e in obj[1]) + \
            ("," if len(obj[1]) == 1 else "") + ")"
    if k == "range":
        return f"[{_math(obj[1])}, {_math(obj[2])}; {_math(obj[3])}]"
    if k == "concat":
        return f"({_math(obj[1])} ⧺ {_math(obj[2])})"
    if k == "repeat":
        return f"({_math(obj[1])})^{_math(obj[2])}"
    if k == "slice":
        a = "·" if obj[2] is None else _math(obj[2])
        b = "·" if obj[3] is None else _math(obj[3])
        return f"{_math(obj[1])}[{a} : {b} : {_math(obj[4])}]"
    if k == "item":
        return f"{_math(obj[1])}[{_math(obj[2])}]"
    if k in _MATH_UN:
        return f"{_MATH_UN[k]}({_math(obj[1])})"
    if k == "rel":
        return f"{_math(obj[2])} {rt._MATH_REL[obj[1]]} {_math(obj[3])}"
    if k == "or":
        return "(" + " ∨ ".join(_math(r) for r in obj[1]) + ")"
    if k == "and":
        return " ∧ ".join(_math(r) for r in obj[1])
    if k == "prog":
        return "; ".join([f"{n} := {_math(t)}" for n, t in obj[1]]
                         + [f"result := {_math(obj[2])}"])
    if k in ("lit", "var", "mask"):
        return rt._math(obj)
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
    if k in rt._MATH_BIN:
        return f"({_math(obj[1])} {rt._MATH_BIN[k]} {_math(obj[2])})"
    raise ValueError(obj)


_LITERAL_KINDS = ("lit", "mask", "str")


def _children(x) -> List[int]:
    """Positions of a node's sub-terms."""
    k = x[0]
    if k in ("lit", "var", "mask", "str"):
        return []
    if k == "tup":
        return []
    if k == "pow":
        return [1]
    if k == "slice":
        return [i for i in (1, 2, 3, 4) if x[i] is not None]
    if k == "range":
        return [1, 2, 3]
    return list(range(1, len(x)))


def _is_value(x) -> bool:
    """Whether a term is already a literal value (needs no step)."""
    k = x[0]
    if k in _LITERAL_KINDS:
        return True
    if k == "tup":
        return all(_is_value(e) for e in x[1])
    if k == "range":
        return all(y[0] == "lit" for y in x[1:])
    return False


def _steps(t, env) -> List[Tuple[str, str]]:
    """Bottom-up evaluation of a closed term: each step's equation realised
    back into language."""
    out: List[Tuple[str, str]] = []

    def go(x):
        if x[0] == "var":
            return value_term(evaluate(x, env))
        if x[0] == "tup":
            return ("tup", tuple(go(e) for e in x[1]))
        if _is_value(x):
            return x
        node = list(x)
        for i in _children(x):
            node[i] = go(x[i])
        node = tuple(node)
        val = value_term(evaluate(node, {}))
        if node != val:
            eq = ("rel", "=", node, val)
            out.append((realise(eq), _math(eq)))
        return val
    go(t)
    return out


def _closed_check(obj) -> None:
    """Refuse a free variable anywhere (the third sort is closed)."""
    bound = set()
    if obj[0] == "prog":
        for name, term in obj[1]:
            _free(term, bound)
            bound.add(name)
        _free(obj[2], bound)
        return
    _free(obj, bound)


def _free(x, bound) -> None:
    if not isinstance(x, tuple) or not x:
        return
    if x[0] == "var":
        if x[1] not in bound:
            raise _nf(f"{x[1]} is free; a term of the third sort has no free "
                      "variables")
        return
    for y in x[1:]:
        if isinstance(y, tuple):
            if y and isinstance(y[0], str):
                _free(y, bound)
            else:
                for z in y:
                    _free(z, bound)


def value_of(obj):
    """The value of a closed term or program, or the truth of a closed
    statement."""
    if obj[0] in ("rel", "and", "or"):
        return holds(obj, {})
    return _value_of(obj)[0]


def _value_of(obj):
    env: Dict[str, object] = {}
    if obj[0] == "prog":
        for name, term in obj[1]:
            env[name] = evaluate(term, env)
        return evaluate(obj[2], env), env
    return evaluate(obj, env), env


def say_third_sort(text: str) -> Optional[Answer]:
    """``say:`` with the third sort, or ``None`` when the text is not read by
    it (so the earlier grammar's refusal stands)."""
    try:
        obj, _ = parse_any(text)
    except ReverseRefusal:
        return None
    try:
        _closed_check(obj)
        col1 = [realise(obj)]
        col2 = [_math(obj)]
        cert: Dict[str, object] = {"kind": "say-seq", "structure": _enc(obj)}
        verdict = "SAID"
        if obj[0] in ("rel", "and", "or"):
            truth = holds(obj, {})
            if obj[0] == "rel":
                a, b = evaluate(obj[2], {}), evaluate(obj[3], {})
                op = obj[1] if truth else _NEGATION[obj[1]]
                eq = ("rel", op, value_term(a), value_term(b))
                col1.append(realise(eq))
                col2.append(_math(eq))
            verdict = "TRUE" if truth else "FALSE"
            cert["truth"] = truth
        elif obj[0] == "prog":
            env: Dict[str, object] = {}
            for name, term in obj[1]:
                for lang, m in _steps(term, env):
                    col1.append(lang)
                    col2.append(m)
                env[name] = evaluate(term, env)
                eq = ("rel", "=", ("var", name), value_term(env[name]))
                col1.append(realise(eq))
                col2.append(_math(eq))
            val = evaluate(obj[2], env)
            if obj[2][0] != "var":
                for lang, m in _steps(obj[2], env):
                    col1.append(lang)
                    col2.append(m)
            eq = ("rel", "=", obj[2], value_term(val))
            col1.append(realise(eq))
            col2.append(_math(eq))
            cert["value"] = _enc(value_term(val))
        else:
            val = evaluate(obj, {})
            for lang, m in _steps(obj, {}):
                col1.append(lang)
                col2.append(m)
            cert["value"] = _enc(value_term(val))
        return Answer("say", verdict, col1[0], col1, col2, cert)
    except ReverseRefusal as exc:
        return rt._refused("say", exc)


# ===========================================================================
# 6.  THE CERTIFICATE ENCODING
# ===========================================================================

def _enc(obj):
    """A JSON-safe copy: a ``Fraction`` as ``"n/d"``, tuples as lists."""
    if isinstance(obj, Fraction):
        return f"{obj.numerator}/{obj.denominator}"
    if isinstance(obj, (tuple, list)):
        return [_enc(x) for x in obj]
    return obj


def _dec(x):
    """Inverse of :func:`_enc` for terms, statements and programs."""
    if x is None:
        return None
    k = x[0]
    if k == "lit":
        n, d = x[1].split("/")
        return ("lit", Fraction(int(n), int(d)))
    if k == "var":
        return ("var", x[1])
    if k in ("mask", "str"):
        return (k, tuple(x[1]))
    if k == "tup":
        return ("tup", tuple(_dec(e) for e in x[1]))
    if k == "pow":
        return ("pow", _dec(x[1]), x[2])
    if k in ("and", "or"):
        return (k, tuple(_dec(r) for r in x[1]))
    if k == "rel":
        return ("rel", x[1], _dec(x[2]), _dec(x[3]))
    if k == "prog":
        return ("prog", tuple((n, _dec(t)) for n, t in x[1]), _dec(x[2]))
    return (k,) + tuple(_dec(y) for y in x[1:])


# ===========================================================================
# 7.  COLUMN 3 -- THE SCRIPT
# ===========================================================================

_SCRIPT = r'''"""Column 3 of a Reverse Three Column Thinking answer (the third sort) --
generated.

Re-reads every column-1 sentence with the declared reader, compares it with
the column-2 structure, and re-derives the claimed value with an evaluator of
its own: strings as lists of code points, its own slice clamping, its own
range arithmetic.  Prints VERIFIED True only if everything holds.
"""
import json
import sys
from fractions import Fraction

sys.path.insert(0, @@ROOT@@)
from glm_universal.reasoning import reverse_tct_seq as rs

DATA = json.loads(@@DATA@@)


class Refused(Exception):
    pass


def F(s):
    n, d = s.split("/")
    return Fraction(int(n), int(d))


def as_int(v):
    if not (isinstance(v, Fraction) and v.denominator == 1):
        raise Refused("not an integer")
    return v.numerator


# A value is ("n", Fraction) | ("m", sorted positions) | ("s", [code points])
# | ("t", [values]) | ("r", start, stop, step).

def elems(v):
    if v[0] == "s":
        return [("s", [c]) for c in v[1]]
    if v[0] == "t":
        return list(v[1])
    if v[0] == "r":
        out, x = [], v[1]
        while (x < v[2]) if v[3] > 0 else (x > v[2]):
            out.append(("n", Fraction(x)))
            x += v[3]
        return out
    raise Refused("not a sequence")


def size(v):
    return len(elems(v)) if v[0] != "s" else len(v[1])


def clamp(n, a, b, c):
    if c == 0:
        raise Refused("zero step")
    lo, hi = (0, n) if c > 0 else (-1, n - 1)
    def fix(x, default):
        if x is None:
            return default
        x = x + n if x < 0 else x
        return lo if x < lo else (hi if x > hi else x)
    i = fix(a, lo if c > 0 else hi)
    j = fix(b, hi if c > 0 else lo)
    out = []
    while (i < j) if c > 0 else (i > j):
        out.append(i)
        i += c
    return out


def eq(a, b):
    if a[0] != b[0]:
        return False
    if a[0] in ("t", "r"):
        x, y = elems(a), elems(b)
        return len(x) == len(y) and all(eq(p, q) for p, q in zip(x, y))
    return a == b


def order(a, b):
    if a[0] == b[0] == "n":
        return (a[1] > b[1]) - (a[1] < b[1])
    if a[0] == b[0] == "s":
        for p, q in zip(a[1], b[1]):
            if p != q:
                return 1 if p > q else -1
        return (len(a[1]) > len(b[1])) - (len(a[1]) < len(b[1]))
    if a[0] == b[0] == "t":
        for p, q in zip(a[1], b[1]):
            if not eq(p, q):
                return order(p, q)
        return (len(a[1]) > len(b[1])) - (len(a[1]) < len(b[1]))
    raise Refused("no order")


def num(v):
    if v[0] != "n":
        raise Refused("not a number")
    return v[1]


def bits(x, y, op):
    w = max(x.bit_length(), y.bit_length()) + 2
    mx, my, out = x % (1 << w), y % (1 << w), 0
    for i in range(w):
        p, q = (mx >> i) & 1, (my >> i) & 1
        out |= int({"band": p and q, "bor": p or q, "bxor": p != q}[op]) << i
    return out - (1 << w) if out >> (w - 1) else out


def ev(t, env):
    k = t[0]
    if k == "lit":
        return ("n", F(t[1]))
    if k == "var":
        return env[t[1]]
    if k == "mask":
        assert all(0 <= p < 24 for p in t[1])
        return ("m", sorted(set(t[1])))
    if k == "str":
        assert all(0 <= c <= 1114111 for c in t[1])
        return ("s", list(t[1]))
    if k == "tup":
        return ("t", [ev(e, env) for e in t[1]])
    if k == "range":
        a, b, c = (as_int(num(ev(x, env))) for x in t[1:])
        if c == 0:
            raise Refused("zero step")
        return ("r", a, b, c)
    if k == "concat":
        a, b = ev(t[1], env), ev(t[2], env)
        if a[0] != b[0] or a[0] not in ("s", "t"):
            raise Refused("sorts")
        return (a[0], list(a[1]) + list(b[1]))
    if k == "repeat":
        s, n = ev(t[1], env), as_int(num(ev(t[2], env)))
        if s[0] not in ("s", "t"):
            raise Refused("sorts")
        out = []
        for _ in range(max(n, 0)):
            out += list(s[1])
        return (s[0], out)
    if k == "slice":
        s = ev(t[1], env)
        a = None if t[2] is None else as_int(num(ev(t[2], env)))
        b = None if t[3] is None else as_int(num(ev(t[3], env)))
        c = as_int(num(ev(t[4], env)))
        idx = clamp(size(s), a, b, c)
        if s[0] == "s":
            return ("s", [s[1][i] for i in idx])
        if s[0] == "t":
            return ("t", [s[1][i] for i in idx])
        if s[0] == "r":
            if not idx:
                return ("r", 0, 0, 1)
            start, step = s[1] + idx[0] * s[3], s[3] * c
            return ("r", start, start + len(idx) * step, step)
        raise Refused("sorts")
    if k == "item":
        s, i = ev(t[1], env), as_int(num(ev(t[2], env)))
        xs = elems(s)
        j = i + len(xs) if i < 0 else i
        if not 0 <= j < len(xs):
            raise Refused("index")
        return xs[j]
    if k == "chr":
        n = as_int(num(ev(t[1], env)))
        if not 0 <= n <= 1114111:
            raise Refused("character")
        return ("s", [n])
    if k == "ord":
        s = ev(t[1], env)
        if s[0] != "s" or len(s[1]) != 1:
            raise Refused("character")
        return ("n", Fraction(s[1][0]))
    if k == "entries":
        return ("t", elems(ev(t[1], env)))
    if k == "length":
        return ("n", Fraction(size(ev(t[1], env))))
    if k == "total":
        s = ev(t[1], env)
        if s[0] == "s":
            raise Refused("sorts")
        return ("n", sum((num(x) for x in elems(s)), Fraction(0)))
    if k in ("least", "greatest"):
        xs = elems(ev(t[1], env))
        if not xs:
            raise Refused("empty")
        best = xs[0]
        for x in xs[1:]:
            o = order(x, best)
            if (o < 0) if k == "least" else (o > 0):
                best = x
        return best
    if k == "neg":
        return ("n", -num(ev(t[1], env)))
    if k == "abs":
        v = num(ev(t[1], env))
        return ("n", v if v >= 0 else -v)
    if k == "compl":
        return ("n", Fraction(-as_int(num(ev(t[1], env))) - 1))
    if k == "size":
        m = ev(t[1], env)
        assert m[0] == "m"
        return ("n", Fraction(len(m[1])))
    if k == "pow":
        b = num(ev(t[1], env))
        if t[2] < 0 and b == 0:
            raise Refused("zero")
        return ("n", b ** t[2])
    a, b = ev(t[1], env), ev(t[2], env)
    if k in ("inter", "union", "symdiff", "setdiff", "dist"):
        assert a[0] == b[0] == "m"
        x, y = set(a[1]), set(b[1])
        r = {"inter": [p for p in x if p in y],
             "union": list(x) + [p for p in y if p not in x],
             "symdiff": [p for p in x if p not in y] + [p for p in y
                                                        if p not in x],
             "setdiff": [p for p in x if p not in y]}
        if k == "dist":
            return ("n", Fraction(len(r["symdiff"])))
        return ("m", sorted(set(r[k])))
    x, y = num(a), num(b)
    if k == "add":
        return ("n", x + y)
    if k == "sub":
        return ("n", x - y)
    if k == "mul":
        return ("n", x * y)
    if k == "min":
        return ("n", x if x <= y else y)
    if k == "max":
        return ("n", x if x >= y else y)
    if k in ("band", "bor", "bxor"):
        return ("n", Fraction(bits(as_int(x), as_int(y), k)))
    if k in ("lshift", "rshift"):
        p, n = as_int(x), as_int(y)
        if n < 0:
            raise Refused("shift")
        return ("n", Fraction(p * 2 ** n if k == "lshift" else p // 2 ** n))
    if y == 0:
        raise Refused("zero")
    if k == "div":
        return ("n", x / y)
    if k == "floordiv":
        return ("n", Fraction((x / y).numerator // (x / y).denominator))
    if k == "mod":
        return ("n", x - y * Fraction((x / y).numerator // (x / y).denominator))
    raise ValueError(k)


def norm(v):
    """A value with every range read out as its entries, for comparison."""
    if v[0] == "r":
        return ("rr", [x[1] for x in elems(v)])
    if v[0] == "t":
        return ("t", [norm(x) for x in v[1]])
    return v


def same_value(mine, claimed):
    return norm(mine) == norm(claimed)


def contains(c, x):
    if c[0] == "m":
        return x[0] == "n" and x[1].denominator == 1 and int(x[1]) in c[1]
    if c[0] == "s":
        if x[0] != "s":
            raise Refused("sorts")
        n, m = len(c[1]), len(x[1])
        return any(c[1][i:i + m] == x[1] for i in range(n - m + 1))
    return any(eq(x, e) for e in elems(c))


def holds(s, env):
    if s[0] == "and":
        return all(holds(r, env) for r in s[1])
    if s[0] == "or":
        return any(holds(r, env) for r in s[1])
    op, a, b = s[1], ev(s[2], env), ev(s[3], env)
    if op in ("in", "notin"):
        return contains(b, a) == (op == "in")
    if op in ("sub", "notsub"):
        return set(a[1]) <= set(b[1]) if op == "sub" else not set(a[1]) <= set(b[1])
    if op in ("=", "!="):
        if a[0] != b[0]:
            raise Refused("sorts")
        return eq(a, b) == (op == "=")
    o = order(a, b)
    return {"<": o < 0, "<=": o <= 0, ">": o > 0, ">=": o >= 0}[op]


def value_of(s):
    if s[0] == "prog":
        env = {}
        for n, t in s[1]:
            env[n] = ev(t, env)
        return ev(s[2], env)
    return ev(s, {})


ok = True
said = [structure for _, structure in DATA["read_back"]]
cert = DATA["certificate"]
if cert["structure"] not in said:
    print("NOT IN COLUMN 1")
    ok = False
for sentence, structure in DATA["read_back"]:
    got = rs._enc(rs.read(sentence))
    if got != structure or rs.realise(rs._dec(structure)) != sentence:
        print("MISMATCH", sentence)
        ok = False
try:
    s = cert["structure"]
    if "truth" in cert:
        ok = ok and holds(s, {}) == cert["truth"]
    if "value" in cert:
        ok = ok and same_value(value_of(s), ev(cert["value"], {}))
except (Refused, AssertionError, ZeroDivisionError, KeyError) as exc:
    print("CHECK FAILED", type(exc).__name__, exc)
    ok = False
print("VERIFIED", ok)
sys.exit(0 if ok else 1)
'''


def _read_back_pairs(a: Answer) -> List[List[object]]:
    out = []
    for s in a.column1:
        try:
            out.append([s, _enc(read(s))])
        except ReverseRefusal:
            continue
    return out


def render_script(a: Answer, root: str, certificate=None) -> str:
    """The column-3 script of a third-sort ``say`` answer."""
    data = {"read_back": _read_back_pairs(a),
            "certificate": a.certificate if certificate is None
            else certificate}
    return (_SCRIPT.replace("@@ROOT@@", repr(root))
            .replace("@@DATA@@", repr(json.dumps(data, sort_keys=True))))


def _mutate_value(v):
    k = v[0]
    if k == "lit":
        n, d = v[1].split("/")
        return ["lit", f"{int(n) + int(d)}/{d}"]
    if k == "str":
        return ["str", list(v[1]) + [33]]
    if k == "tup":
        return ["tup", list(v[1]) + [["lit", "0/1"]]]
    if k == "range":
        if len(evaluate(_dec(v), {})) == 0:
            return ["range", ["lit", "0/1"], ["lit", "1/1"], ["lit", "1/1"]]
        return ["range", _mutate_value(v[1]), v[2], v[3]]
    if k == "mask":
        held = set(v[1])
        return ["mask", sorted(held - {0} if 0 in held else held | {0})]
    return None


def mutated_script(a: Answer, root: str) -> Optional[str]:
    """The same script with the claim changed: it must fail."""
    c = json.loads(json.dumps(a.certificate))
    if "truth" in c:
        c["truth"] = not c["truth"]
    elif "value" in c:
        m = _mutate_value(c["value"])
        if m is None:
            return None
        c["value"] = m
    else:
        return None
    return render_script(a, root, c)


# ===========================================================================
# 8.  THE BATTERY (T3)
# ===========================================================================

def battery_terms(atoms: Sequence[str]) -> List:
    """Every term of depth at most two over ``atoms`` (dialect source) with
    the sequence operators: depth one applies each operator to atoms, depth
    two applies each to depth-one terms and atoms."""
    base = [from_source(a) for a in atoms]
    one = ("lit", Fraction(1))
    two = ("lit", Fraction(2))
    neg = ("lit", Fraction(-1))

    def unary(x):
        return [("length", x), ("entries", x), ("item", x, ("lit",
                                                             Fraction(0))),
                ("slice", x, None, None, neg), ("slice", x, one, None, one),
                ("repeat", x, two), ("least", x), ("total", x)]

    def binary(x, y):
        return [("concat", x, y)]
    depth1 = []
    for x in base:
        depth1 += unary(x)
    for x in base:
        for y in base:
            depth1 += binary(x, y)
    depth2 = []
    for x in depth1:
        if x[0] in ("length", "least", "total"):
            depth2.append(("chr", x))
            continue
        depth2 += unary(x)
    pool = base + depth1
    for x in depth1[:40]:
        for y in pool[:12]:
            depth2 += binary(x, y)
    seen, out = set(), []
    for t in base + depth1 + depth2:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out
