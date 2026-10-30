"""``glm_universal.reasoning.reverse_tct_imp`` -- the imperative grammar.

Phase 95 (``studies/IMPERATIVE_GRAMMAR_STUDY.md``).  The reverse grammar of
Phases 67-69 and the third sort of Phase 94 speak terms, statements and
``let`` programs.  This module speaks **programs with state**: assignment,
simultaneous assignment, ``for`` and ``while`` loops, branches, conditional
expressions, functions (with recursion) and ``match``.  Every construct is
spelled head first, and every list of steps, names, parameters, arguments,
cases or patterns states its count before its items -- the discipline of the
mask and sequence literals, which ``RequestProject/GLM/ImperativeGrammar.lean``
proves uniquely readable for any grammar of that shape.

The grammar is asked for by ``say:`` only, and only after the earlier grammar
and the third sort have both failed to *read* the text
(:func:`reverse_tct.say`), so no earlier answer can change.

Terms and conditions are the earlier sorts'.  Every term the earlier
realisers spell is spelled here through them: a node's children are realised
by this module (so that a nested call, choice or reserved name is spelled the
imperative way) and spliced into the earlier template.

Exact throughout: ``Fraction``, code points and ``int``; no float, no clock,
no randomness.  Every step and loop round is counted against
:data:`STEP_LIMIT` and every call against :data:`DEPTH_LIMIT`; exceeding
either is a named refusal, never an answer.
"""

from __future__ import annotations

import ast
import json
import sys
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import reverse_tct as rt
from . import reverse_tct_seq as rs
from .reverse_tct import Answer, ReverseRefusal, number_words

__all__ = ["IMP_WORDS", "IMP_RESERVED", "STEP_LIMIT", "DEPTH_LIMIT",
           "TRACE_LIMIT", "SIZE_LIMIT", "realise", "realise_term", "read", "from_source",
           "parse_any", "run", "say_imperative", "render_script",
           "mutated_script", "battery_programs", "Function"]

#: Steps (statements executed and loop rounds) a program may take.
STEP_LIMIT = 100_000
#: Calls a program may nest.
DEPTH_LIMIT = 200
#: Assignments outside any call traced in column 1.
TRACE_LIMIT = 24
#: Bits a numerator or denominator, and characters a string, may hold.
SIZE_LIMIT = 4096

#: The words the imperative grammar adds.
IMP_WORDS = frozenset({
    "program", "steps", "step", "set", "together", "names", "to", "for",
    "each", "in", "while", "do", "nothing", "if", "otherwise", "return",
    "define", "parameters", "parameter", "as", "match", "against", "cases",
    "case", "provided", "literal", "anything", "name", "one", "patterns",
    "pattern", "sequence", "call", "on", "arguments", "argument", "choice",
    "when", "else", "nonzero", "no", "variable", "result", "is"})
#: Words no name may be spelled bare.
IMP_RESERVED = rs.SEQ_RESERVED | IMP_WORDS

#: Calls the earlier sorts read as terms; a program may not redefine them.
_BUILTINS = frozenset({"Fraction", "frozenset", "abs", "hamming", "len",
                       "ord", "chr", "tuple", "range", "min", "max", "sum",
                       "pow"})
#: The dialect's prelude, which this grammar does not hold.
_PRELUDE = frozenset({"unit", "classify", "golay_encode", "ds_bits", "plane",
                      "divmod", "list", "sorted", "print", "str", "int"})


def _unreadable(msg: str) -> ReverseRefusal:
    return ReverseRefusal("UNREADABLE", msg)


def _nf(msg: str) -> ReverseRefusal:
    return ReverseRefusal("NOT_IN_FRAGMENT", msg)


def _mismatch(msg: str) -> ReverseRefusal:
    return ReverseRefusal("SORT_MISMATCH", msg)


# ===========================================================================
# 1.  THE REALISER (column 2 -> column 1)
# ===========================================================================

def name_words(x: str) -> List[str]:
    """A name: bare, or ``the variable x`` when x is a grammar word."""
    return ["the", "variable", x] if x in IMP_RESERVED else [x]


def _counted(items: Sequence[List[str]], singular: str, plural: str,
             sep: str = ",") -> List[str]:
    out = number_words(len(items)) + [singular if len(items) == 1
                                      else plural]
    for i, ws in enumerate(items):
        if i:
            out.append(sep)
        out += ws
    return out


def _ph(i: int) -> str:
    return f"\x00{i}\x01"


def _split(t):
    """``(node with placeholder children, {placeholder: child})``."""
    subs: Dict[str, object] = {}

    def ph(x):
        key = _ph(len(subs))
        subs[key] = x
        return ("var", key)
    k = t[0]
    if k == "tup":
        return ("tup", tuple(ph(e) for e in t[1])), subs
    if k == "pow":
        return ("pow", ph(t[1]), t[2]), subs
    if k == "slice":
        return ("slice", ph(t[1]), None if t[2] is None else ph(t[2]),
                None if t[3] is None else ph(t[3]), ph(t[4])), subs
    if k == "rel":
        return ("rel", t[1], ph(t[2]), ph(t[3])), subs
    return (k,) + tuple(ph(x) for x in t[1:]), subs


def realise_term(t) -> List[str]:
    """Column 1 of one term, as a token list."""
    k = t[0]
    if k == "var":
        return name_words(t[1])
    if k == "call":
        args = [realise_term(a) for a in t[2]]
        tail = (["no", "arguments"] if not args
                else _counted(args, "argument", "arguments"))
        return ["the", "call", "of"] + name_words(t[1]) + ["on"] + tail
    if k == "choice":
        return (["the", "choice", "of"] + realise_term(t[1]) + ["when"]
                + realise_cond(t[2]) + [",", "else"] + realise_term(t[3]))
    if k in ("lit", "mask", "str"):
        return rs.realise_term(t)
    node, subs = _split(t)
    out: List[str] = []
    for w in rs.realise_term(node):
        out += realise_term(subs[w]) if w in subs else [w]
    return out


def _realise_rel(r) -> List[str]:
    return realise_term(r[2]) + rt._RELATIONS[r[1]] + realise_term(r[3])


def _realise_clause(c) -> List[str]:
    if c[0] == "rel":
        return _realise_rel(c)
    if c[0] == "truthy":
        return realise_term(c[1]) + ["is", "nonzero"]
    out = ["either"]
    for i, r in enumerate(c[1]):
        if i:
            out += [",", "or"]
        out += _realise_clause(r)
    return out


def realise_cond(c) -> List[str]:
    """Column 1 of a condition (an earlier statement, or *T is nonzero*)."""
    if c[0] == "and":
        out: List[str] = []
        for i, r in enumerate(c[1]):
            if i:
                out += [",", "and"]
            out += _realise_clause(r)
        return out
    return _realise_clause(c)


def realise_block(b) -> List[str]:
    if not b:
        return ["do", "nothing"]
    return (["do"] + _count_words(len(b), "step", "steps") + [":"]
            + _join_items([realise_stmt(s) for s in b], ";"))


def _join_items(items: Sequence[List[str]], sep: str) -> List[str]:
    out: List[str] = []
    for i, ws in enumerate(items):
        if i:
            out.append(sep)
        out += ws
    return out


def _count_words(n: int, singular: str, plural: str) -> List[str]:
    return number_words(n) + [singular if n == 1 else plural]


def realise_pattern(p) -> List[str]:
    k = p[0]
    if k == "plit":
        return ["the", "literal"] + realise_term(p[1])
    if k == "pany":
        return ["anything"]
    if k == "pname":
        return ["the", "name"] + name_words(p[1])
    if k == "por":
        return (["one", "of"] + _count_words(len(p[1]), "pattern", "patterns")
                + _join_items([realise_pattern(q) for q in p[1]], ","))
    if k == "pseq":
        return (["the", "sequence", "of"]
                + _count_words(len(p[1]), "pattern", "patterns")
                + _join_items([realise_pattern(q) for q in p[1]], ","))
    raise ValueError(f"not a pattern: {p!r}")


def realise_stmt(s) -> List[str]:
    k = s[0]
    if k == "set":
        return ["set"] + name_words(s[1]) + ["to"] + realise_term(s[2])
    if k == "setall":
        return (["set", "together"] + _count_words(len(s[1]), "name", "names")
                + _join_items([name_words(x) for x in s[1]], ",") + ["to"]
                + _join_items([realise_term(t) for t in s[2]], ","))
    if k == "for":
        return (["for", "each"] + name_words(s[1]) + ["in"]
                + realise_term(s[2]) + [","] + realise_block(s[3]))
    if k == "while":
        return ["while"] + realise_cond(s[1]) + [","] + realise_block(s[2])
    if k == "if":
        return (["if"] + realise_cond(s[1]) + [","] + realise_block(s[2])
                + ["otherwise"] + realise_block(s[3]))
    if k == "return":
        return ["return"] + realise_term(s[1])
    if k == "define":
        params = (["no", "parameters"] if not s[2] else
                  _count_words(len(s[2]), "parameter", "parameters")
                  + _join_items([name_words(x) for x in s[2]], ","))
        return (["define"] + name_words(s[1]) + ["of"] + params + ["as"]
                + realise_block(s[3]))
    if k == "match":
        cases = []
        for _, pat, guard, block in s[2]:
            ws = ["in", "case"] + realise_pattern(pat)
            if guard is not None:
                ws += ["provided"] + realise_cond(guard)
            cases.append(ws + [","] + realise_block(block))
        return (["match"] + realise_term(s[1]) + ["against"]
                + _count_words(len(cases), "case", "cases") + [":"]
                + _join_items(cases, ";"))
    raise ValueError(f"not a statement: {s!r}")


def _join(toks: Sequence[str]) -> str:
    out = ""
    for t in toks:
        if t in (",", ".", ":", ";"):
            out += t
        else:
            out += (" " if out else "") + t
    return out


def realise(obj) -> str:
    """Column 1 of a program, a condition or a term, as one string."""
    k = obj[0]
    if k == "impprog":
        toks = (["the", "program", "of"]
                + _count_words(len(obj[1]), "step", "steps") + [":"]
                + _join_items([realise_stmt(s) for s in obj[1]], ";")
                + [".", "the", "result", "is"] + realise_term(obj[2]) + ["."])
        return _join(toks)
    if k in ("rel", "and", "or", "truthy"):
        return _join(realise_cond(obj))
    return _join(realise_term(obj))


# ===========================================================================
# 2.  THE READER (column 1 -> column 2)
# ===========================================================================

def _tokens(text: str) -> List[str]:
    for p in (",", ".", ":", ";"):
        text = text.replace(p, f" {p} ")
    return text.split()


class _ImpReader(rs._SeqReader):
    """The third sort's reader, with the imperative grammar's heads."""

    def name(self) -> str:
        if self.ahead(("the", "variable")):
            self.expect("the", "variable")
            w = self.peek()
            if w is None or not w.isidentifier() or w not in IMP_RESERVED:
                raise _unreadable("'the variable' names only a grammar word; "
                                  "any other name is spelled bare")
            self.i += 1
            return w
        w = self.peek()
        if w is None or not w.isidentifier() or w in IMP_RESERVED:
            raise _unreadable(f"a name was expected at {w!r}")
        self.i += 1
        return w

    def count(self, singular: str, plural: str, least: int = 1) -> int:
        k = self.natural()
        if k < least:
            raise _unreadable(f"at least {least} {plural} are spelled here")
        self.expect(singular if k == 1 else plural)
        return k

    def items(self, k: int, item, sep: str = ","):
        out = []
        for j in range(k):
            if j:
                self.expect(sep)
            out.append(item())
        return tuple(out)

    def term(self):
        t = self.peek()
        if t == "the":
            if self.ahead(("the", "variable")):
                return ("var", self.name())
            if self.ahead(("the", "call", "of")):
                self.expect("the", "call", "of")
                f = self.name()
                self.expect("on")
                if self.ahead(("no", "arguments")):
                    self.expect("no", "arguments")
                    return ("call", f, ())
                k = self.count("argument", "arguments")
                return ("call", f, self.items(k, self.term))
            if self.ahead(("the", "choice", "of")):
                self.expect("the", "choice", "of")
                a = self.term()
                self.expect("when")
                c = self.condition()
                self.expect(",", "else")
                return ("choice", a, c, self.term())
        if (t is not None and t.isidentifier() and t in IMP_WORDS
                and t not in rs.SEQ_RESERVED):
            raise _unreadable(f"{t!r} is a grammar word and names no variable")
        return super().term()

    def simple_statement(self):
        a = self.term()
        if self.ahead(("is", "nonzero")):
            self.expect("is", "nonzero")
            return ("truthy", a)
        op = self.relation()
        return ("rel", op, a, self.term())

    def condition(self):
        s = self.statement()
        if s[0] == "and" and any(r[0] == "truthy" for r in s[1]):
            raise _unreadable("'is nonzero' stands alone as a condition")
        return s

    def block(self):
        self.expect("do")
        if self.peek() == "nothing":
            self.expect("nothing")
            return ()
        k = self.count("step", "steps")
        self.expect(":")
        return self.items(k, self.stmt, ";")

    def pattern(self):
        if self.ahead(("the", "literal")):
            self.expect("the", "literal")
            v = self.term()
            if v[0] not in ("lit", "str"):
                raise _unreadable("a literal pattern holds a number or a "
                                  "string literal")
            return ("plit", v)
        if self.peek() == "anything":
            self.expect("anything")
            return ("pany",)
        if self.ahead(("the", "name")):
            self.expect("the", "name")
            return ("pname", self.name())
        if self.ahead(("one", "of")):
            self.expect("one", "of")
            k = self.count("pattern", "patterns", 2)
            return ("por", self.items(k, self.pattern))
        if self.ahead(("the", "sequence", "of")):
            self.expect("the", "sequence", "of")
            k = self.count("pattern", "patterns")
            return ("pseq", self.items(k, self.pattern))
        raise _unreadable(f"a pattern was expected at {self.peek()!r}")

    def case(self):
        self.expect("in", "case")
        p = self.pattern()
        guard = None
        if self.peek() == "provided":
            self.expect("provided")
            guard = self.condition()
        self.expect(",")
        return ("case", p, guard, self.block())

    def stmt(self):
        t = self.peek()
        if t == "set":
            if self.peek(1) == "together":
                self.expect("set", "together")
                k = self.count("name", "names", 2)
                names = self.items(k, self.name)
                self.expect("to")
                return ("setall", names, self.items(k, self.term))
            self.expect("set")
            x = self.name()
            self.expect("to")
            return ("set", x, self.term())
        if t == "for":
            self.expect("for", "each")
            x = self.name()
            self.expect("in")
            it = self.term()
            self.expect(",")
            return ("for", x, it, self.block())
        if t == "while":
            self.expect("while")
            c = self.condition()
            self.expect(",")
            return ("while", c, self.block())
        if t == "if":
            self.expect("if")
            c = self.condition()
            self.expect(",")
            yes = self.block()
            self.expect("otherwise")
            return ("if", c, yes, self.block())
        if t == "return":
            self.expect("return")
            return ("return", self.term())
        if t == "define":
            self.expect("define")
            f = self.name()
            self.expect("of")
            if self.ahead(("no", "parameters")):
                self.expect("no", "parameters")
                params: Tuple[str, ...] = ()
            else:
                k = self.count("parameter", "parameters")
                params = self.items(k, self.name)
            self.expect("as")
            return ("define", f, params, self.block())
        if t == "match":
            self.expect("match")
            subject = self.term()
            self.expect("against")
            k = self.count("case", "cases")
            self.expect(":")
            return ("match", subject, self.items(k, self.case, ";"))
        raise _unreadable(f"a step was expected at {t!r}")

    def imp_program(self):
        self.expect("the", "program", "of")
        k = self.count("step", "steps")
        self.expect(":")
        stmts = self.items(k, self.stmt, ";")
        self.expect(".", "the", "result", "is")
        res = self.term()
        self.expect(".")
        return ("impprog", stmts, res)


def read(text: str):
    """Column 2 of a sentence of the imperative grammar: a program, a
    condition or a term."""
    toks = _tokens(text)
    if not toks:
        raise _unreadable("the empty sentence")
    if toks[:3] == ["the", "program", "of"]:
        r = _ImpReader(toks)
        obj = r.imp_program()
        r.done()
        return obj
    last: Optional[ReverseRefusal] = None
    for kind in ("condition", "term"):
        r = _ImpReader(toks)
        try:
            obj = getattr(r, kind)()
            r.done()
        except ReverseRefusal as exc:
            last = exc
            continue
        return obj
    raise last if last is not None else _unreadable(text)


# ===========================================================================
# 3.  COLUMN 3 IN -- THE DIALECT'S SYNTAX
# ===========================================================================

_SEQ = ("s", "t", "r")


def _ast_sort(node, sorts: Dict[str, str]) -> Optional[str]:
    """The sort of an expression decided before the program runs, or
    ``None``."""
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, bool):
            return None
        if isinstance(v, int):
            return "n"
        if isinstance(v, str):
            return "s"
        return None
    if isinstance(node, ast.Name):
        return sorts.get(node.id)
    if isinstance(node, ast.Tuple):
        return "t"
    if isinstance(node, ast.UnaryOp):
        return "n" if not isinstance(node.op, ast.Not) else None
    if isinstance(node, ast.BinOp):
        a, b = _ast_sort(node.left, sorts), _ast_sort(node.right, sorts)
        if isinstance(node.op, (ast.Add, ast.Mult)):
            for x in (a, b):
                if x in ("s", "t"):
                    return x
            return "n" if a == b == "n" else None
        return "n" if a == "n" and b == "n" else None
    if isinstance(node, ast.Subscript):
        s = _ast_sort(node.value, sorts)
        if isinstance(node.slice, ast.Slice):
            return s if s in _SEQ else None
        return {"s": "s", "r": "n"}.get(s or "")
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        f = node.func.id
        if f in ("Fraction", "len", "ord", "abs", "sum", "hamming", "pow"):
            return "n"
        if f == "chr":
            return "s"
        if f == "tuple":
            return "t"
        if f == "range":
            return "r"
        return None
    if isinstance(node, ast.IfExp):
        a, b = _ast_sort(node.body, sorts), _ast_sort(node.orelse, sorts)
        return a if a == b else None
    return None


def _assignments(body, out: List[Tuple[str, object]], poisoned: set) -> None:
    """Every ``(name, expression)`` assignment of a program; a loop variable
    is paired with ``("iter", expression)``; parameters and pattern captures
    are poisoned (their sort is never decided)."""
    for st in body:
        if isinstance(st, ast.Assign) and len(st.targets) == 1:
            t = st.targets[0]
            if isinstance(t, ast.Name):
                out.append((t.id, st.value))
            elif (isinstance(t, ast.Tuple) and isinstance(st.value, ast.Tuple)
                  and len(t.elts) == len(st.value.elts)):
                for n, v in zip(t.elts, st.value.elts):
                    if isinstance(n, ast.Name):
                        out.append((n.id, v))
        elif isinstance(st, ast.AugAssign) and isinstance(st.target, ast.Name):
            out.append((st.target.id, ast.BinOp(
                left=ast.Name(id=st.target.id, ctx=ast.Load()), op=st.op,
                right=st.value)))
        elif isinstance(st, ast.For) and isinstance(st.target, ast.Name):
            out.append((st.target.id, ("iter", st.iter)))
            _assignments(st.body, out, poisoned)
        elif isinstance(st, (ast.While, ast.If)):
            _assignments(st.body, out, poisoned)
            _assignments(st.orelse, out, poisoned)
        elif isinstance(st, ast.FunctionDef):
            for a in st.args.args:
                poisoned.add(a.arg)
            _assignments(st.body, out, poisoned)
        elif isinstance(st, ast.Match):
            for c in st.cases:
                for n in ast.walk(c.pattern):
                    if isinstance(n, ast.MatchAs) and n.name:
                        poisoned.add(n.name)
                _assignments(c.body, out, poisoned)


def infer_sorts(body) -> Dict[str, str]:
    """A name takes a sort when every assignment to it has that sort
    (flow-insensitive, iterated to its fixed point)."""
    pairs: List[Tuple[str, object]] = []
    poisoned: set = set()
    _assignments(body, pairs, poisoned)
    sorts: Dict[str, str] = {}
    names = sorted({n for n, _ in pairs} - poisoned)
    for _ in range(len(names) + 1):
        changed = False
        for n in names:
            if n in sorts:
                continue
            got = set()
            for m, v in pairs:
                if m != n:
                    continue
                if isinstance(v, tuple) and v and v[0] == "iter":
                    s = _ast_sort(v[1], sorts)
                    got.add({"s": "s", "r": "n"}.get(s or ""))
                else:
                    got.add(_ast_sort(v, sorts))
            if len(got) == 1 and None not in got:
                sorts[n] = got.pop()
                changed = True
        if not changed:
            break
    return sorts


def _sort_of_term(t, sorts: Dict[str, str]) -> Optional[str]:
    """The decided sort of a translated term (used for ``+``, ``*`` and
    ``len``)."""
    k = t[0]
    if k == "lit":
        return "n"
    if k == "str":
        return "s"
    if k == "tup":
        return "t"
    if k == "range":
        return "r"
    if k == "mask":
        return "m"
    if k == "var":
        return sorts.get(t[1])
    if k in ("concat", "repeat"):
        for x in t[1:]:
            s = _sort_of_term(x, sorts)
            if s in ("s", "t"):
                return s
        return None
    if k == "slice":
        s = _sort_of_term(t[1], sorts)
        return s if s in _SEQ else None
    if k == "item":
        return {"s": "s", "r": "n"}.get(_sort_of_term(t[1], sorts) or "")
    if k == "chr":
        return "s"
    if k == "entries":
        return "t"
    if k in ("call", "least", "greatest"):
        return None
    if k == "choice":
        a, b = _sort_of_term(t[1], sorts), _sort_of_term(t[3], sorts)
        return a if a == b else None
    if k in ("add", "mul"):
        a, b = _sort_of_term(t[1], sorts), _sort_of_term(t[2], sorts)
        return "n" if a == b == "n" else None
    return "n"


class _ImpSource(rs._Source):
    """Reads dialect source into the imperative grammar's structure."""

    def __init__(self, sorts: Dict[str, str], functions: set) -> None:
        super().__init__()
        self.sorts = sorts
        self.functions = functions

    def sort(self, t) -> str:
        s = _sort_of_term(t, self.sorts)
        return s if s is not None else "?"

    def term(self, node):
        if isinstance(node, ast.Name):
            if not node.id.isidentifier():
                raise _nf(f"the name {node.id!r}")
            return ("var", node.id)
        if isinstance(node, ast.IfExp):
            return ("choice", self.term(node.body), self.cond(node.test),
                    self.term(node.orelse))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            f = node.func.id
            if f in self.functions:
                if node.keywords or any(isinstance(a, ast.Starred)
                                        for a in node.args):
                    raise _nf(f"keyword or starred arguments to {f}")
                return ("call", f, tuple(self.term(a) for a in node.args))
            if f == "Fraction" and not node.keywords and node.args:
                ints = [rt._int_const(a) for a in node.args]
                if len(node.args) <= 2 and not all(v is not None
                                                   for v in ints):
                    if any(isinstance(a, ast.Constant)
                           and isinstance(a.value, str) for a in node.args):
                        raise _nf("Fraction read from a string")
                    a = self.term(node.args[0])
                    b = (self.term(node.args[1]) if len(node.args) == 2
                         else ("lit", Fraction(1)))
                    return ("div", a, b)
            if f not in _BUILTINS:
                raise _nf(f"the call {f}(...)")
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            raise _nf("true division: CPython gives a float for two "
                      "integers, which no term holds; Fraction(a, b) is the "
                      "exact quotient")
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            n = rt._int_const(node.right)
            if n is not None and n < 0:
                raise _nf("a negative power: CPython gives a float for an "
                          "integer base")
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add,
                                                                ast.Mult)):
            a, b = self.term(node.left), self.term(node.right)
            sa, sb = self.sort(a), self.sort(b)
            if isinstance(node.op, ast.Add):
                if sa in ("s", "t") or sb in ("s", "t"):
                    return ("concat", a, b)
                return ("add", a, b)
            if sa in ("s", "t"):
                return ("repeat", a, b)
            if sb in ("s", "t"):
                return ("repeat", b, a)
            return ("mul", a, b)
        return super().term(node)

    def call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "len" and \
                len(node.args) == 1 and not node.keywords:
            s = self.term(node.args[0])
            return ("size", s) if self.sort(s) == "m" else ("length", s)
        return super().call(node)

    def cond(self, node):
        cnf = self.statement(node)
        if cnf is None:
            return ("truthy", self.term(node))
        return rt._from_clauses(cnf)

    # -- statements ---------------------------------------------------------

    def block(self, body, in_function: bool, top: bool = False):
        out = []
        for st in body:
            out.append(self.stmt(st, in_function, top))
        return tuple(out)

    def stmt(self, st, in_function: bool, top: bool = False):
        if isinstance(st, ast.Assign):
            if len(st.targets) != 1:
                raise _nf("a chained assignment")
            t = st.targets[0]
            if isinstance(t, ast.Name):
                return ("set", t.id, self.term(st.value))
            if (isinstance(t, ast.Tuple) and isinstance(st.value, ast.Tuple)
                    and len(t.elts) == len(st.value.elts) >= 2
                    and all(isinstance(e, ast.Name) for e in t.elts)):
                return ("setall", tuple(e.id for e in t.elts),
                        tuple(self.term(v) for v in st.value.elts))
            raise _nf("an assignment to other than a name or a tuple of names "
                      "from a tuple of the same length")
        if isinstance(st, ast.AugAssign):
            if not isinstance(st.target, ast.Name):
                raise ReverseRefusal("MUTABLE_CONTAINER", "an augmented "
                                     "assignment to other than a name")
            node = ast.BinOp(left=ast.Name(id=st.target.id, ctx=ast.Load()),
                             op=st.op, right=st.value)
            return ("set", st.target.id, self.term(node))
        if isinstance(st, ast.For):
            if st.orelse or not isinstance(st.target, ast.Name):
                raise _nf("a for loop with an else, or over other than one "
                          "name")
            it = self.term(st.iter)
            if self.sort(it) == "m":
                raise ReverseRefusal("ORDER_UNDEFINED", "a loop over a mask: "
                                     "a set has no declared order")
            return ("for", st.target.id, it, self.block(st.body, in_function))
        if isinstance(st, ast.While):
            if st.orelse:
                raise _nf("a while loop with an else")
            return ("while", self.cond(st.test),
                    self.block(st.body, in_function))
        if isinstance(st, ast.If):
            return ("if", self.cond(st.test), self.block(st.body, in_function),
                    self.block(st.orelse, in_function))
        if isinstance(st, ast.Return):
            if not in_function:
                raise _nf("a return outside a function")
            if st.value is None:
                raise _nf("a return without a value")
            return ("return", self.term(st.value))
        if isinstance(st, ast.FunctionDef):
            if not top:
                raise _nf("a function defined inside a block or a function")
            a = st.args
            if (a.posonlyargs or a.vararg or a.kwonlyargs or a.kwarg
                    or a.defaults or st.decorator_list):
                raise _nf("a function with other than plain positional "
                          "parameters")
            params = tuple(x.arg for x in a.args)
            if len(set(params)) != len(params):
                raise _nf("a repeated parameter")
            return ("define", st.name, params, self.block(st.body, True))
        if isinstance(st, ast.Match):
            cases = []
            for i, c in enumerate(st.cases):
                p = self.pattern(c.pattern)
                g = None if c.guard is None else self.cond(c.guard)
                if g is None and _irrefutable(p) and i < len(st.cases) - 1:
                    raise _nf("an irrefutable case before the last (CPython "
                              "rejects it)")
                cases.append(("case", p, g, self.block(c.body, in_function)))
            return ("match", self.term(st.subject), tuple(cases))
        raise _nf(f"the statement {type(st).__name__}")

    def pattern(self, p):
        if isinstance(p, ast.MatchValue):
            v = p.value
            if isinstance(v, ast.Constant) and isinstance(v.value, bool):
                raise _nf("a boolean pattern")
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                return ("plit", ("str", tuple(ord(c) for c in v.value)))
            n = rt._int_const(v)
            if n is None:
                raise _nf("a value pattern other than an integer or a string")
            return ("plit", ("lit", Fraction(n)))
        if isinstance(p, ast.MatchAs):
            if p.pattern is not None:
                raise _nf("an 'as' pattern")
            return ("pany",) if p.name is None else ("pname", p.name)
        if isinstance(p, ast.MatchOr):
            alts = tuple(self.pattern(q) for q in p.patterns)
            if any(_captures(q) for q in alts):
                raise _nf("a capture inside an or-pattern")
            return ("por", alts)
        if isinstance(p, ast.MatchSequence):
            if not p.patterns or any(isinstance(q, ast.MatchStar)
                                     for q in p.patterns):
                raise _nf("an empty or starred sequence pattern")
            return ("pseq", tuple(self.pattern(q) for q in p.patterns))
        raise _nf(f"the pattern {type(p).__name__}")


def _captures(p) -> bool:
    if p[0] == "pname":
        return True
    if p[0] in ("por", "pseq"):
        return any(_captures(q) for q in p[1])
    return False


def _irrefutable(p) -> bool:
    if p[0] in ("pany", "pname"):
        return True
    if p[0] == "por":
        return any(_irrefutable(q) for q in p[1])
    return False


def from_source(source: str):
    """Column 2 of a dialect program with state."""
    try:
        tree = ast.parse(source.strip())
    except SyntaxError as exc:
        raise _nf(f"not Python: {exc.msg}") from None
    body = tree.body
    if len(body) < 2 or not isinstance(body[-1], ast.Expr):
        raise _nf("a program is steps, then its result expression")
    functions = {st.name for st in body if isinstance(st, ast.FunctionDef)}
    clash = functions & (_BUILTINS | _PRELUDE)
    if clash:
        raise _nf(f"a function named like a builtin: {sorted(clash)[0]}")
    reader = _ImpSource(infer_sorts(body[:-1]), functions)
    stmts = reader.block(body[:-1], False, top=True)
    return ("impprog", stmts, reader.term(body[-1].value))


def parse_any(text: str):
    """Column 2 of ``text``: a sentence if it is one, else dialect source."""
    if _tokens(text)[:3] == ["the", "program", "of"]:
        return read(text), "language"
    return from_source(text), "source"


# ===========================================================================
# 4.  COLUMN 2 -- RUNNING THE PROGRAM
# ===========================================================================

class Function:
    """A function value: never a term, never printed."""

    def __init__(self, name: str, params: Tuple[str, ...], body,
                 local_names: frozenset) -> None:
        self.name = name
        self.params = params
        self.body = body
        self.local_names = local_names


def _locals_of(params, body) -> frozenset:
    """CPython's rule: every name bound anywhere in the body is local."""
    out = set(params)

    def walk(b):
        for s in b:
            k = s[0]
            if k == "set":
                out.add(s[1])
            elif k == "setall":
                out.update(s[1])
            elif k == "for":
                out.add(s[1])
                walk(s[3])
            elif k == "while":
                walk(s[2])
            elif k == "if":
                walk(s[2])
                walk(s[3])
            elif k == "match":
                for _, p, _, blk in s[2]:
                    out.update(_pattern_names(p))
                    walk(blk)
    walk(body)
    return frozenset(out)


def _pattern_names(p) -> List[str]:
    if p[0] == "pname":
        return [p[1]]
    if p[0] in ("por", "pseq"):
        return [n for q in p[1] for n in _pattern_names(q)]
    return []


class _Frame:
    def __init__(self, fn: Optional[Function], values: Dict[str, object]):
        self.fn = fn
        self.values = values


def _check_size(v) -> None:
    """Refuse a value too large to speak: a value past :data:`SIZE_LIMIT`
    is a named refusal, never an answer (nor a crash in the realiser)."""
    if isinstance(v, tuple):
        for e in v:
            _check_size(e)
        return
    if isinstance(v, bool):
        return
    if isinstance(v, int):
        big = v.bit_length() > SIZE_LIMIT
    elif isinstance(v, Fraction):
        big = (v.numerator.bit_length() > SIZE_LIMIT
               or v.denominator.bit_length() > SIZE_LIMIT)
    elif isinstance(v, str):
        big = len(v) > SIZE_LIMIT
    else:
        return
    if big:
        raise ReverseRefusal("SIZE_LIMIT", f"a value larger than {SIZE_LIMIT} "
                             "bits or characters")


class Machine:
    """The interpreter: exact values, counted steps, bounded depth and
    bounded value size."""

    def __init__(self, step_limit: int = STEP_LIMIT,
                 depth_limit: int = DEPTH_LIMIT) -> None:
        self.step_limit = step_limit
        self.depth_limit = depth_limit
        self.steps = 0
        self.depth = 0
        self.globals: Dict[str, object] = {}
        self.order: List[str] = []
        self.trace: List[Tuple[str, object]] = []

    def tick(self) -> None:
        self.steps += 1
        if self.steps > self.step_limit:
            raise ReverseRefusal("STEP_LIMIT", f"more than {self.step_limit} "
                                 "steps")

    def lookup(self, name: str, fr: _Frame):
        if fr.fn is not None and name in fr.fn.local_names:
            if name not in fr.values:
                raise ReverseRefusal("UNBOUND", f"{name} is read before it is "
                                     f"assigned in {fr.fn.name}")
            return fr.values[name]
        if name not in self.globals:
            raise ReverseRefusal("UNBOUND", f"{name} is read before any "
                                 "assignment")
        return self.globals[name]

    def assign(self, name: str, v, fr: _Frame) -> None:
        if isinstance(v, Function):
            raise _mismatch("a function is not a value to assign")
        _check_size(v)
        if fr.fn is not None:
            fr.values[name] = v
            return
        if name not in self.globals:
            self.order.append(name)
        self.globals[name] = v
        if len(self.trace) < TRACE_LIMIT:
            self.trace.append((name, v))

    # -- terms --------------------------------------------------------------

    def value(self, t, fr: _Frame):
        k = t[0]
        if k == "var":
            return self.lookup(t[1], fr)
        if k == "call":
            return self.call(t, fr)
        if k == "choice":
            return self.value(t[1] if self.holds(t[2], fr) else t[3], fr)
        if k in ("lit", "mask", "str"):
            return rs.evaluate(t, {})
        if k == "tup":
            return tuple(self.value(e, fr) for e in t[1])
        node, subs = _split(t)
        vals = {key: self.value(x, fr) for key, x in subs.items()}
        for v in vals.values():
            if isinstance(v, Function):
                raise _mismatch("a function is not a value")
        closed = _replace(node, {key: rs.value_term(v)
                                 for key, v in vals.items()})
        out = rs.evaluate(closed, {})
        _check_size(out)
        return out

    def call(self, t, fr: _Frame):
        f = self.lookup(t[1], fr)
        if not isinstance(f, Function):
            raise _mismatch(f"{t[1]} is not a function")
        args = [self.value(a, fr) for a in t[2]]
        if len(args) != len(f.params):
            raise ReverseRefusal("ARITY", f"{f.name} takes {len(f.params)} "
                                 f"arguments, not {len(args)}")
        for v in args:
            if isinstance(v, Function):
                raise _mismatch("a function is not an argument")
        if self.depth + 1 > self.depth_limit:
            raise ReverseRefusal("DEPTH_LIMIT", f"calls nested more than "
                                 f"{self.depth_limit} deep")
        self.depth += 1
        try:
            got = self.block(f.body, _Frame(f, dict(zip(f.params, args))))
        finally:
            self.depth -= 1
        if got is None:
            raise ReverseRefusal("NO_RESULT", f"{f.name} returns nothing; "
                                 "CPython's None has no term")
        return got[1]

    def holds(self, c, fr: _Frame) -> bool:
        k = c[0]
        if k == "truthy":
            v = self.value(c[1], fr)
            if rs._vsort(v) != "n" or isinstance(v, Function):
                raise _mismatch("'is nonzero' reads a number; the truth of a "
                                "string, a tuple or a range is not read")
            return v != 0
        if k == "and":
            return all(self.holds(r, fr) for r in c[1])
        if k == "or":
            return any(self.holds(r, fr) for r in c[1])
        a, b = self.value(c[2], fr), self.value(c[3], fr)
        if isinstance(a, Function) or isinstance(b, Function):
            raise _mismatch("a function is not compared")
        return rs.holds(("rel", c[1], rs.value_term(a), rs.value_term(b)), {})

    # -- statements ---------------------------------------------------------

    def block(self, b, fr: _Frame):
        for s in b:
            got = self.stmt(s, fr)
            if got is not None:
                return got
        return None

    def stmt(self, s, fr: _Frame):
        self.tick()
        k = s[0]
        if k == "set":
            self.assign(s[1], self.value(s[2], fr), fr)
            return None
        if k == "setall":
            vals = [self.value(t, fr) for t in s[2]]
            for n, v in zip(s[1], vals):
                self.assign(n, v, fr)
            return None
        if k == "for":
            it = self.value(s[2], fr)
            sort = rs._vsort(it)
            if sort == "m":
                raise ReverseRefusal("ORDER_UNDEFINED", "a loop over a mask: "
                                     "a set has no declared order")
            if sort not in _SEQ:
                raise _mismatch("a loop runs over a string, a tuple or a "
                                "range")
            items = (Fraction(x) for x in it) if sort == "r" else iter(it)
            for x in items:
                self.tick()
                self.assign(s[1], x, fr)
                got = self.block(s[3], fr)
                if got is not None:
                    return got
            return None
        if k == "while":
            while self.holds(s[1], fr):
                self.tick()
                got = self.block(s[2], fr)
                if got is not None:
                    return got
            return None
        if k == "if":
            return self.block(s[2] if self.holds(s[1], fr) else s[3], fr)
        if k == "return":
            return ("return", self.value(s[1], fr))
        if k == "define":
            if s[1] not in self.globals:
                self.order.append(s[1])
            self.globals[s[1]] = Function(s[1], s[2], s[3],
                                          _locals_of(s[2], s[3]))
            return None
        if k == "match":
            v = self.value(s[1], fr)
            for _, p, guard, blk in s[2]:
                bound = self.match(p, v)
                if bound is None:
                    continue
                for n, x in bound:
                    self.assign(n, x, fr)
                if guard is not None and not self.holds(guard, fr):
                    continue
                return self.block(blk, fr)
            return None
        raise ValueError(f"not a statement: {s!r}")

    def match(self, p, v) -> Optional[List[Tuple[str, object]]]:
        k = p[0]
        if k == "pany":
            return []
        if k == "pname":
            return [(p[1], v)]
        if k == "plit":
            want = rs.evaluate(p[1], {})
            if isinstance(v, Function) or rs._vsort(v) != rs._vsort(want):
                return None
            return [] if rs._equal(v, want) else None
        if k == "por":
            for q in p[1]:
                got = self.match(q, v)
                if got is not None:
                    return got
            return None
        if k == "pseq":
            if isinstance(v, Function) or rs._vsort(v) not in ("t", "r"):
                return None
            items = [Fraction(x) for x in v] if isinstance(v, range) \
                else list(v)
            if len(items) != len(p[1]):
                return None
            out: List[Tuple[str, object]] = []
            for q, x in zip(p[1], items):
                got = self.match(q, x)
                if got is None:
                    return None
                out += got
            return out
        raise ValueError(f"not a pattern: {p!r}")


def _replace(node, values: Dict[str, object]):
    """Replace every placeholder child of ``node`` by its value term."""
    def sub(x):
        if isinstance(x, tuple) and len(x) == 2 and x[0] == "var" \
                and x[1] in values:
            return values[x[1]]
        return x
    k = node[0]
    if k == "tup":
        return ("tup", tuple(sub(e) for e in node[1]))
    if k == "pow":
        return ("pow", sub(node[1]), node[2])
    if k == "rel":
        return ("rel", node[1], sub(node[2]), sub(node[3]))
    return (k,) + tuple(None if x is None else sub(x) for x in node[1:])


def run(obj, step_limit: int = STEP_LIMIT, depth_limit: int = DEPTH_LIMIT):
    """Run a program: ``(value, machine)``."""
    m = Machine(step_limit, depth_limit)
    top = _Frame(None, {})
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 40 * depth_limit + 2000))
    try:
        m.block(obj[1], top)
        val = m.value(obj[2], top)
    except RecursionError:
        raise ReverseRefusal("DEPTH_LIMIT", "the interpreter's own stack") \
            from None
    finally:
        sys.setrecursionlimit(old)
    if isinstance(val, Function):
        raise _mismatch("a function is not a result")
    _check_size(val)
    return val, m


# ===========================================================================
# 5.  SAY -- COLUMN 1 GENERATED, WITH THE VALUE
# ===========================================================================

def _math_term(t) -> str:
    k = t[0]
    if k == "var":
        return t[1]
    if k == "call":
        return f"{t[1]}(" + ", ".join(_math_term(a) for a in t[2]) + ")"
    if k == "choice":
        return (f"({_math_term(t[1])} if {_math_cond(t[2])} else "
                f"{_math_term(t[3])})")
    if k in ("lit", "mask", "str"):
        return rs._math(t)
    node, subs = _split(t)
    text = rs._math(node)
    for key, x in subs.items():
        text = text.replace(key, _math_term(x))
    return text


def _math_cond(c) -> str:
    k = c[0]
    if k == "truthy":
        return f"{_math_term(c[1])} ≠ 0"
    if k == "and":
        return " ∧ ".join(_math_cond(r) for r in c[1])
    if k == "or":
        return "(" + " ∨ ".join(_math_cond(r) for r in c[1]) + ")"
    return f"{_math_term(c[2])} {rt._MATH_REL[c[1]]} {_math_term(c[3])}"


def _math_pattern(p) -> str:
    k = p[0]
    if k == "plit":
        return _math_term(p[1])
    if k == "pany":
        return "_"
    if k == "pname":
        return p[1]
    if k == "por":
        return " | ".join(_math_pattern(q) for q in p[1])
    return "(" + ", ".join(_math_pattern(q) for q in p[1]) + ")"


def _math_block(b) -> str:
    return "{ " + "; ".join(_math_stmt(s) for s in b) + " }" if b else "{ }"


def _math_stmt(s) -> str:
    k = s[0]
    if k == "set":
        return f"{s[1]} := {_math_term(s[2])}"
    if k == "setall":
        return (f"({', '.join(s[1])}) := ("
                + ", ".join(_math_term(t) for t in s[2]) + ")")
    if k == "for":
        return f"for {s[1]} ∈ {_math_term(s[2])} {_math_block(s[3])}"
    if k == "while":
        return f"while {_math_cond(s[1])} {_math_block(s[2])}"
    if k == "if":
        return (f"if {_math_cond(s[1])} {_math_block(s[2])} else "
                f"{_math_block(s[3])}")
    if k == "return":
        return f"return {_math_term(s[1])}"
    if k == "define":
        return f"{s[1]}({', '.join(s[2])}) := {_math_block(s[3])}"
    cases = []
    for _, p, g, b in s[2]:
        head = _math_pattern(p) + ("" if g is None else
                                   f" if {_math_cond(g)}")
        cases.append(f"{head} ⇒ {_math_block(b)}")
    return f"match {_math_term(s[1])} {{ " + " | ".join(cases) + " }"


def math(obj) -> str:
    """Column 2's rendering of a program, a condition or a term."""
    if obj[0] == "impprog":
        return "; ".join([_math_stmt(s) for s in obj[1]]
                         + [f"result := {_math_term(obj[2])}"])
    if obj[0] in ("rel", "and", "or", "truthy"):
        return _math_cond(obj)
    return _math_term(obj)


def _eq(left, v):
    return ("rel", "=", left, rs.value_term(v))


def say_imperative(text: str, step_limit: int = STEP_LIMIT,
                   depth_limit: int = DEPTH_LIMIT) -> Optional[Answer]:
    """``say:`` with the imperative grammar, or ``None`` when the text is not
    read by it (so the earlier refusal stands)."""
    try:
        obj, _ = parse_any(text)
    except ReverseRefusal:
        return None
    try:
        val, m = run(obj, step_limit, depth_limit)
        col1 = [realise(obj)]
        col2 = [math(obj)]
        trace, finals = [], []
        for name, v in m.trace:
            eq = _eq(("var", name), v)
            col1.append(realise(eq))
            col2.append(math(eq))
            trace.append([name, rs._enc(rs.value_term(v))])
        for name in m.order:
            v = m.globals[name]
            if isinstance(v, Function):
                continue
            eq = _eq(("var", name), v)
            col1.append(realise(eq))
            col2.append(math(eq))
            finals.append([name, rs._enc(rs.value_term(v))])
        eq = _eq(obj[2], val)
        col1.append(realise(eq))
        col2.append(math(eq))
        cert: Dict[str, object] = {
            "kind": "say-imp", "structure": _enc(obj),
            "value": rs._enc(rs.value_term(val)), "trace": trace,
            "finals": finals, "steps": m.steps}
        return Answer("say", "SAID", col1[0], col1, col2, cert)
    except ReverseRefusal as exc:
        return rt._refused("say", exc)


def value_of(obj, step_limit: int = STEP_LIMIT,
             depth_limit: int = DEPTH_LIMIT):
    """The value of a program (refusals raised)."""
    return run(obj, step_limit, depth_limit)[0]


# ===========================================================================
# 6.  THE CERTIFICATE ENCODING
# ===========================================================================

def _enc(obj):
    return rs._enc(obj)


def _dec_term(x):
    if x is None:
        return None
    k = x[0]
    if k == "call":
        return ("call", x[1], tuple(_dec_term(a) for a in x[2]))
    if k == "choice":
        return ("choice", _dec_term(x[1]), _dec_cond(x[2]), _dec_term(x[3]))
    if k == "var":
        return ("var", x[1])
    if k in ("lit", "mask", "str", "pow"):
        return rs._dec(x)
    if k == "tup":
        return ("tup", tuple(_dec_term(e) for e in x[1]))
    return (k,) + tuple(_dec_term(y) for y in x[1:])


def _dec_cond(x):
    k = x[0]
    if k == "truthy":
        return ("truthy", _dec_term(x[1]))
    if k in ("and", "or"):
        return (k, tuple(_dec_cond(r) for r in x[1]))
    return ("rel", x[1], _dec_term(x[2]), _dec_term(x[3]))


def _dec_pattern(x):
    k = x[0]
    if k == "plit":
        return ("plit", _dec_term(x[1]))
    if k == "pany":
        return ("pany",)
    if k == "pname":
        return ("pname", x[1])
    return (k, tuple(_dec_pattern(q) for q in x[1]))


def _dec_block(b):
    return tuple(_dec_stmt(s) for s in b)


def _dec_stmt(x):
    k = x[0]
    if k == "set":
        return ("set", x[1], _dec_term(x[2]))
    if k == "setall":
        return ("setall", tuple(x[1]), tuple(_dec_term(t) for t in x[2]))
    if k == "for":
        return ("for", x[1], _dec_term(x[2]), _dec_block(x[3]))
    if k == "while":
        return ("while", _dec_cond(x[1]), _dec_block(x[2]))
    if k == "if":
        return ("if", _dec_cond(x[1]), _dec_block(x[2]), _dec_block(x[3]))
    if k == "return":
        return ("return", _dec_term(x[1]))
    if k == "define":
        return ("define", x[1], tuple(x[2]), _dec_block(x[3]))
    return ("match", _dec_term(x[1]),
            tuple(("case", _dec_pattern(p), None if g is None
                   else _dec_cond(g), _dec_block(b))
                  for _, p, g, b in x[2]))


def _dec(x):
    """Inverse of :func:`_enc` for programs, conditions and terms."""
    k = x[0]
    if k == "impprog":
        return ("impprog", _dec_block(x[1]), _dec_term(x[2]))
    if k in ("rel", "and", "or", "truthy"):
        return _dec_cond(x)
    return _dec_term(x)


# ===========================================================================
# 7.  COLUMN 3 -- THE SCRIPT
# ===========================================================================

def _base_evaluator() -> str:
    """The third sort's own script evaluator, lifted out of its script and
    renamed, so that this script's ``ev`` and ``holds`` sit in front of it
    and every recursion passes through them."""
    src = rs._SCRIPT
    body = src[src.index("class Refused(Exception):"):src.index("\nok = True")]
    body = body.replace("def ev(t, env):", "def ev_base(t, env):")
    body = body.replace("def holds(s, env):", "def holds_base(s, env):")
    body = body.replace("def value_of(s):", "def _unused_value_of(s):")
    return body


_SCRIPT_HEAD = r'''"""Column 3 of a Reverse Three Column Thinking answer (the imperative
grammar) -- generated.

Re-reads every column-1 sentence with the declared reader, compares it with
the column-2 structure, and replays the program with an interpreter of its
own (the third sort's own term evaluator underneath): every traced
assignment, every final value and the result must be what column 1 claims.
Prints VERIFIED True only if everything holds.
"""
import json
import sys
from fractions import Fraction

sys.path.insert(0, @@ROOT@@)
sys.setrecursionlimit(200000)
from glm_universal.reasoning import reverse_tct_imp as ri

DATA = json.loads(@@DATA@@)
STEPS = 10 * @@STEPS@@
DEPTH = 10 * @@DEPTH@@
TRACE = @@TRACE@@

'''

_SCRIPT_TAIL = r'''

class Fn:
    def __init__(self, name, params, body):
        self.name, self.params, self.body = name, params, body
        self.local = set(params)
        def walk(b):
            for s in b:
                if s[0] == "set":
                    self.local.add(s[1])
                elif s[0] == "setall":
                    self.local.update(s[1])
                elif s[0] == "for":
                    self.local.add(s[1])
                    walk(s[3])
                elif s[0] == "while":
                    walk(s[2])
                elif s[0] == "if":
                    walk(s[2])
                    walk(s[3])
                elif s[0] == "match":
                    for c in s[2]:
                        self.local.update(names(c[1]))
                        walk(c[3])
        walk(body)


def names(p):
    if p[0] == "pname":
        return [p[1]]
    if p[0] in ("por", "pseq"):
        return [n for q in p[1] for n in names(q)]
    return []


class Frame:
    def __init__(self, fn, values):
        self.fn, self.values = fn, values


G = {}
ORDER = []
REPLAY = []
COUNT = [0, 0]


def tick():
    COUNT[0] += 1
    if COUNT[0] > STEPS:
        raise Refused("steps")


def get(name, fr):
    if fr.fn is not None and name in fr.fn.local:
        return fr.values[name]
    return G[name]


def put(name, v, fr):
    assert not isinstance(v, Fn)
    if fr.fn is not None:
        fr.values[name] = v
        return
    if name not in G:
        ORDER.append(name)
    G[name] = v
    if len(REPLAY) < TRACE:
        REPLAY.append((name, v))


def ev(t, fr):
    k = t[0]
    if k == "var":
        return get(t[1], fr)
    if k == "call":
        f = get(t[1], fr)
        assert isinstance(f, Fn) and len(f.params) == len(t[2])
        args = [ev(a, fr) for a in t[2]]
        COUNT[1] += 1
        if COUNT[1] > DEPTH:
            raise Refused("depth")
        try:
            got = run(f.body, Frame(f, dict(zip(f.params, args))))
        finally:
            COUNT[1] -= 1
        assert got is not None
        return got[1]
    if k == "choice":
        return ev(t[1] if holds(t[2], fr) else t[3], fr)
    return ev_base(t, fr)


def holds(s, fr):
    if s[0] == "truthy":
        v = ev(s[1], fr)
        if v[0] != "n":
            raise Refused("truthy")
        return v[1] != 0
    return holds_base(s, fr)


def seq_items(v):
    if v[0] in ("s", "t", "r"):
        return elems(v)
    raise Refused("not a sequence")


def matches(p, v):
    if p[0] == "pany":
        return []
    if p[0] == "pname":
        return [(p[1], v)]
    if p[0] == "plit":
        w = ev(p[1], Frame(None, {}))
        return [] if (v[0] == w[0] and eq(v, w)) else None
    if p[0] == "por":
        for q in p[1]:
            got = matches(q, v)
            if got is not None:
                return got
        return None
    if v[0] not in ("t", "r"):
        return None
    xs = elems(v)
    if len(xs) != len(p[1]):
        return None
    out = []
    for q, x in zip(p[1], xs):
        got = matches(q, x)
        if got is None:
            return None
        out += got
    return out


def run(block, fr):
    for s in block:
        tick()
        k = s[0]
        if k == "set":
            put(s[1], ev(s[2], fr), fr)
        elif k == "setall":
            vals = [ev(t, fr) for t in s[2]]
            for n, v in zip(s[1], vals):
                put(n, v, fr)
        elif k == "for":
            for x in seq_items(ev(s[2], fr)):
                tick()
                put(s[1], x, fr)
                got = run(s[3], fr)
                if got is not None:
                    return got
        elif k == "while":
            while holds(s[1], fr):
                tick()
                got = run(s[2], fr)
                if got is not None:
                    return got
        elif k == "if":
            got = run(s[2] if holds(s[1], fr) else s[3], fr)
            if got is not None:
                return got
        elif k == "return":
            return ("return", ev(s[1], fr))
        elif k == "define":
            if s[1] not in G:
                ORDER.append(s[1])
            G[s[1]] = Fn(s[1], s[2], s[3])
        elif k == "match":
            v = ev(s[1], fr)
            for c in s[2]:
                bound = matches(c[1], v)
                if bound is None:
                    continue
                for n, x in bound:
                    put(n, x, fr)
                if c[2] is not None and not holds(c[2], fr):
                    continue
                got = run(c[3], fr)
                if got is not None:
                    return got
                break
        else:
            raise Refused("statement")
    return None


def literal(x):
    return ev(x, Frame(None, {}))


ok = True
cert = DATA["certificate"]
said = [structure for _, structure in DATA["read_back"]]
if cert["structure"] not in said:
    print("NOT IN COLUMN 1")
    ok = False
for sentence, structure in DATA["read_back"]:
    got = ri._enc(ri.read(sentence))
    if got != structure or ri.realise(ri._dec(structure)) != sentence:
        print("MISMATCH", sentence)
        ok = False
try:
    prog = cert["structure"]
    top = Frame(None, {})
    run(prog[1], top)
    result = ev(prog[2], top)
    ok = ok and same_value(result, literal(cert["value"]))
    if len(REPLAY) != len(cert["trace"]):
        print("TRACE LENGTH")
        ok = False
    for (n, v), (cn, cv) in zip(REPLAY, cert["trace"]):
        if n != cn or not same_value(v, literal(cv)):
            print("TRACE", cn)
            ok = False
    finals = [(n, G[n]) for n in ORDER if not isinstance(G[n], Fn)]
    if [n for n, _ in finals] != [n for n, _ in cert["finals"]]:
        print("FINAL NAMES")
        ok = False
    for (n, v), (cn, cv) in zip(finals, cert["finals"]):
        if not same_value(v, literal(cv)):
            print("FINAL", cn)
            ok = False
except (Refused, AssertionError, ZeroDivisionError, KeyError,
        RecursionError) as exc:
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
    """The column-3 script of an imperative ``say`` answer."""
    data = {"read_back": _read_back_pairs(a),
            "certificate": a.certificate if certificate is None
            else certificate}
    head = (_SCRIPT_HEAD.replace("@@ROOT@@", repr(root))
            .replace("@@DATA@@", repr(json.dumps(data, sort_keys=True)))
            .replace("@@STEPS@@", str(STEP_LIMIT))
            .replace("@@DEPTH@@", str(DEPTH_LIMIT))
            .replace("@@TRACE@@", str(TRACE_LIMIT)))
    return head + _base_evaluator() + _SCRIPT_TAIL


def mutated_script(a: Answer, root: str) -> Optional[str]:
    """The same script with the claimed value changed: it must fail."""
    c = json.loads(json.dumps(a.certificate))
    m = rs._mutate_value(c["value"])
    if m is None:
        return None
    c["value"] = m
    return render_script(a, root, c)


# ===========================================================================
# 8.  THE BATTERY (I5)
# ===========================================================================

def battery_programs() -> List:
    """Programs built from the declared statement shapes: every shape of
    statement over a set of terms, conditions and patterns, alone and nested
    one level inside every block-bearing shape, each followed by a result.
    The programs need not run; the battery measures reading back."""
    one, two = ("lit", Fraction(1)), ("lit", Fraction(2))
    x, total = ("var", "x"), ("var", "total")
    terms = [x, total, one, ("lit", Fraction(-1, 2)), ("str", (97, 98)),
             ("tup", (one, x)), ("call", "f", (x,)), ("call", "g", ()),
             ("call", "f", (one, ("call", "f", (x,)))),
             ("choice", one, ("rel", "<", x, two), two),
             ("add", x, ("call", "f", (total,))),
             ("range", ("lit", Fraction(0)), x, one),
             ("item", ("var", "s"), ("lit", Fraction(0)))]
    conds = [("rel", "<", x, two), ("truthy", x), ("truthy", total),
             ("and", (("rel", "<", x, two), ("rel", ">=", total, one))),
             ("or", (("rel", "=", x, one), ("rel", "in", x,
                                                ("tup", (one, two))))),
             ("rel", "=", ("call", "f", (x,)), ("choice", one, ("truthy", x),
                                                 two))]
    pats = [("plit", one), ("plit", ("str", (97,))), ("pany",),
            ("pname", "y"), ("pname", "total"),
            ("por", (("plit", one), ("plit", two))),
            ("pseq", (("pname", "a"), ("pany",))),
            ("pseq", (("pseq", (("plit", one),)), ("pname", "b")))]
    simple = []
    for t in terms:
        simple.append(("set", "x", t))
        simple.append(("set", "total", t))
        simple.append(("return", t))
    simple.append(("setall", ("x", "y"), (one, two)))
    simple.append(("setall", ("a", "total", "c"), (x, total, one)))

    def shapes(inner):
        out = []
        blocks = [(), (inner,), (inner, ("set", "x", one))]
        for b in blocks[1:]:
            out.append(("for", "k", terms[11], b))
            out.append(("for", "total", ("str", (97,)), b))
            for c in conds:
                out.append(("while", c, b))
        for c in conds:
            for b1 in blocks[1:]:
                for b2 in blocks:
                    out.append(("if", c, b1, b2))
        for p in pats:
            out.append(("match", x, (("case", p, None, (inner,)),)))
            out.append(("match", x, (("case", p, conds[0], (inner,)),
                                     ("case", ("pany",), None, ()))))
        out.append(("define", "f", ("n",), (inner,)))
        out.append(("define", "f", (), (inner, inner)))
        out.append(("define", "total", ("a", "total"), (inner,)))
        return out
    depth1 = list(simple)
    for s in simple[::4]:
        depth1 += shapes(s)
    programs = []
    for s in depth1:
        programs.append(("impprog", (s,), x))
    for s in depth1[::7]:
        for r in terms[::3]:
            programs.append(("impprog", (s, ("set", "x", one)), r))
    seen, out = set(), []
    for p in programs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out
