"""``glm_universal.reasoning.python_speech`` -- the GLM speaking Python.

The measuring half of ``studies/PYTHON_SPEECH_STUDY.md``.

:func:`speak` takes a small Python program -- expressions, assignments,
``if``/``for``/``while``, pure ``def`` functions, ``match``/``case`` -- and
evaluates it exactly on the substrate, returning a Three Column Thinking
payload:

1. **Language.** One sentence per operation: what was done, on which layer.
2. **Mathematics.** The same step as an exact equation over ``Q``, ``Z`` or
   ``F_2`` (slices as index maps, bitwise operations as register runs,
   classifications as Hamming distances).
3. **Re-derivation script.** A self-contained script, standard library only,
   that re-checks every step of column 2 with CPython's own operators,
   re-runs the whole program under CPython with the plain-Python prelude,
   and prints ``VERIFIED True`` only if every check and the final value
   agree. :func:`verify_payload` runs it with ``python3 -I`` in a fresh
   process.

The evaluator is written against the substrate, not delegated to Python:
bitwise operations run the Toffoli/Fredkin programs of
:mod:`.python_substrate` lane by lane; shifts are dyadic multiplications;
slices are computed index maps; set algebra is mask algebra; ``classify`` is
the complete Golay decoder. Integer and rational arithmetic is Python's own
exact ``int`` and ``Fraction`` arithmetic, which *is* the rational layer.

Whenever an answer would need a float, a non-deterministic source, a tie at
the deep hole, a distance beyond the packing radius, a comparison across
units, an order CPython does not promise, or more work than the budget, the
payload is a **named refusal** instead (:data:`.python_substrate.
REFUSAL_NAMES`). A refusal carries its own certificate where one exists,
and its column 3 checks that certificate.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import python_substrate as ps
from .python_substrate import PythonRefusal

__all__ = [
    "Step", "Quantity", "SpeechPayload", "Evaluator", "speak",
    "literal", "render_script", "verify_payload", "mutated_script",
    "static_refusal", "python_speech_report",
]

#: The dialect's builtins; any other free name is a ``NameError``.
BUILTINS: Tuple[str, ...] = (
    "len", "abs", "sum", "max", "min", "divmod", "pow", "ord", "chr",
    "tuple", "frozenset", "range", "Fraction", "int", "bool", "unit",
    "classify", "golay_encode", "hamming", "ds_bits", "plane",
    "nearest", "resolve", "agree", "resolve_unsure",
    "decode_confidence", "agree_confidence",
    "resolve_at", "agree_at", "resolve_floor", "agree_floor",
    "decode_soft", "decode_soft_floor", "agree_soft",
)
FLOAT_NAMES = ("float", "complex")
NONDETERMINISTIC_NAMES = ("hash", "id", "input", "globals", "locals", "vars",
                          "dir")
NONDETERMINISTIC_MODULES = ("random", "time", "secrets", "os", "uuid",
                            "datetime", "sys")
MUTABLE_NODES = (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.SetComp,
                 ast.DictComp)

MAX_STEPS = 4000
MAX_COST = 200_000
MAX_DEPTH = 80
MAX_POWER_BITS = 1 << 20


# ===========================================================================
# 1.  VALUES THE DIALECT ADDS
# ===========================================================================

@dataclass(frozen=True)
class Quantity:
    """``unit(value, name)``: an exact value with a declared unit."""

    value: object
    name: str


@dataclass(frozen=True)
class _Function:
    name: str
    params: Tuple[str, ...]
    body: Tuple[ast.stmt, ...]


@dataclass(frozen=True)
class _Builtin:
    name: str


@dataclass(frozen=True)
class _Module:
    name: str


@dataclass(frozen=True)
class _Method:
    attr: str
    receiver: int


class _Return(Exception):
    def __init__(self, value) -> None:
        super().__init__()
        self.value = value


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


def _is_int(v) -> bool:
    return isinstance(v, int)                       # bool included


def _is_num(v) -> bool:
    return isinstance(v, (int, Fraction))


def _tname(v) -> str:
    return "Quantity" if isinstance(v, Quantity) else type(v).__name__


def literal(v) -> str:
    """A Python literal that rebuilds ``v`` exactly under the prelude."""
    if isinstance(v, bool) or v is None:
        return repr(v)
    if isinstance(v, int):
        return repr(v)
    if isinstance(v, Fraction):
        return f"Fraction({v.numerator}, {v.denominator})"
    if isinstance(v, str):
        return repr(v)
    if isinstance(v, tuple):
        inner = ", ".join(literal(x) for x in v)
        return f"({inner},)" if len(v) == 1 else f"({inner})"
    if isinstance(v, frozenset):
        if not v:
            return "frozenset()"
        return "frozenset({" + ", ".join(repr(x) for x in sorted(v)) + "})"
    if isinstance(v, range):
        return f"range({v.start}, {v.stop}, {v.step})"
    if isinstance(v, Quantity):
        return f"unit({literal(v.value)}, {v.name!r})"
    raise PythonRefusal("UNSUPPORTED", f"a {_tname(v)} has no literal")


def _decimal7(q: Fraction) -> str:
    """``q`` rounded half-up to seven places, for column 1 only (column 2
    and the script carry the exact fraction)."""
    scaled = (Fraction(q) * 10 ** 7 + Fraction(1, 2)) // 1
    whole, frac = divmod(int(scaled), 10 ** 7)
    return f"{whole}.{frac:07d}"


def _m(v) -> str:
    """The value as column 2 writes it."""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, Fraction):
        return f"{v.numerator}/{v.denominator}"
    return literal(v)


# ===========================================================================
# 2.  THE STATIC GATE
# ===========================================================================

def static_refusal(tree: ast.AST) -> Optional[PythonRefusal]:
    """Refusals decided from the text alone, before anything runs.

    A float or complex literal anywhere -- even in a branch that would not
    run -- is refused: the contract forbids IEEE-754 values in the program,
    not only in the path taken. The same holds for importing a
    non-deterministic module or naming ``hash``, ``id`` or ``input``.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value,
                                                         (float, complex)):
            return PythonRefusal(
                "FLOAT", f"line {node.lineno}: an IEEE-754 literal "
                         f"{node.value!r} (directive D7)")
        if isinstance(node, ast.Name) and node.id in FLOAT_NAMES:
            return PythonRefusal("FLOAT", f"line {node.lineno}: {node.id}() "
                                          "makes an IEEE-754 value")
        if isinstance(node, ast.Name) and node.id in NONDETERMINISTIC_NAMES:
            return PythonRefusal(
                "NONDETERMINISTIC",
                f"line {node.lineno}: {node.id}() depends on the process "
                "(hash seed, memory layout or input), so a re-derivation "
                "could not reproduce it")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(
                node, ast.Import) else [node.module or ""]
            for name in names:
                if name.split(".")[0] in NONDETERMINISTIC_MODULES:
                    return PythonRefusal(
                        "NONDETERMINISTIC",
                        f"line {node.lineno}: module {name} brings in "
                        "randomness, clocks or the environment")
    return None


# ===========================================================================
# 3.  THE EVALUATOR
# ===========================================================================

@dataclass(frozen=True)
class Step:
    """One operation, stated three ways."""

    layer: str
    language: str
    math: str
    check: str


class Evaluator:
    """Runs one program exactly, recording a :class:`Step` per operation."""

    def __init__(self, max_steps: int = MAX_STEPS,
                 max_cost: int = MAX_COST) -> None:
        self.max_steps = max_steps
        self.max_cost = max_cost
        self.steps: List[Step] = []
        self.cost = 0
        self.depth = 0
        self.globals: Dict[str, object] = {}
        self.certificate: Optional[str] = None
        self.error_class: Optional[str] = None

    # -- bookkeeping ------------------------------------------------------
    def step(self, layer: str, language: str, math: str, check: str) -> None:
        self.steps.append(Step(layer, language, math, check))
        if len(self.steps) > self.max_steps:
            raise PythonRefusal("BUDGET", f"more than {self.max_steps} "
                                          "operations; termination is not "
                                          "decided, so the run is stopped")

    def tick(self, n: int = 1) -> None:
        self.cost += n
        if self.cost > self.max_cost:
            raise PythonRefusal("BUDGET", f"step cost above {self.max_cost}")

    def error(self, cls: str, message: str) -> PythonRefusal:
        self.error_class = cls
        return PythonRefusal("PYTHON_ERROR", f"{cls}: {message}")

    # -- programs ---------------------------------------------------------
    def run(self, source: str):
        tree = ast.parse(source)
        refusal = static_refusal(tree)
        if refusal is not None:
            raise refusal
        body = list(tree.body)
        last = None
        if body and isinstance(body[-1], ast.Expr):
            last = body.pop().value
        self.exec_block(body, self.globals)
        if last is None:
            return None
        value = self.eval(last, self.globals)
        if isinstance(value, (_Function, _Builtin, _Module, _Method)):
            raise PythonRefusal("UNSUPPORTED", "a function is not a value "
                                               "the dialect returns")
        return value

    def exec_block(self, stmts: Sequence[ast.stmt], env: Dict) -> None:
        for s in stmts:
            self.exec_stmt(s, env)

    def exec_stmt(self, s: ast.stmt, env: Dict) -> None:
        if isinstance(s, ast.Expr):
            self.eval(s.value, env)
        elif isinstance(s, ast.Assign):
            value = self.eval(s.value, env)
            for target in s.targets:
                self.bind(target, value, env)
        elif isinstance(s, ast.AnnAssign) and s.value is not None:
            self.bind(s.target, self.eval(s.value, env), env)
        elif isinstance(s, ast.AugAssign):
            if not isinstance(s.target, ast.Name):
                raise PythonRefusal("MUTABLE_CONTAINER",
                                    "only names are rebound in place")
            old = self.lookup(s.target.id, env)
            self.bind(s.target, self.binop(s.op, old, self.eval(s.value, env)),
                      env)
        elif isinstance(s, ast.If):
            if self.truth(self.eval(s.test, env)):
                self.exec_block(s.body, env)
            else:
                self.exec_block(s.orelse, env)
        elif isinstance(s, ast.While):
            if s.orelse:
                raise PythonRefusal("UNSUPPORTED", "while ... else")
            while self.truth(self.eval(s.test, env)):
                self.tick()
                try:
                    self.exec_block(s.body, env)
                except _Break:
                    break
                except _Continue:
                    continue
        elif isinstance(s, ast.For):
            if s.orelse:
                raise PythonRefusal("UNSUPPORTED", "for ... else")
            for item in self.iterate(self.eval(s.iter, env)):
                self.tick()
                self.bind(s.target, item, env)
                try:
                    self.exec_block(s.body, env)
                except _Break:
                    break
                except _Continue:
                    continue
        elif isinstance(s, ast.Break):
            raise _Break()
        elif isinstance(s, ast.Continue):
            raise _Continue()
        elif isinstance(s, ast.Pass):
            pass
        elif isinstance(s, ast.Return):
            raise _Return(None if s.value is None else self.eval(s.value, env))
        elif isinstance(s, ast.FunctionDef):
            a = s.args
            if (s.decorator_list or a.vararg or a.kwarg or a.kwonlyargs
                    or a.defaults or a.posonlyargs):
                raise PythonRefusal("UNSUPPORTED", "only plain positional "
                                                   "parameters")
            env[s.name] = _Function(s.name, tuple(p.arg for p in a.args),
                                    tuple(s.body))
        elif isinstance(s, ast.Match):
            self.exec_match(s, env)
        elif isinstance(s, ast.Assert):
            if not self.truth(self.eval(s.test, env)):
                raise self.error("AssertionError", "assertion failed")
        elif isinstance(s, ast.ImportFrom) and s.module == "fractions":
            env["Fraction"] = _Builtin("Fraction")
        elif isinstance(s, ast.Import) and all(
                a.name == "fractions" for a in s.names):
            env["fractions"] = _Module("fractions")
        else:
            raise PythonRefusal("UNSUPPORTED",
                                f"statement {type(s).__name__}")

    def bind(self, target: ast.expr, value, env: Dict) -> None:
        if isinstance(target, ast.Name):
            env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            items = list(self.iterate(value))
            if len(items) != len(target.elts):
                raise self.error("ValueError", f"cannot unpack "
                                 f"{len(items)} values into "
                                 f"{len(target.elts)}")
            for t, v in zip(target.elts, items):
                self.bind(t, v, env)
        else:
            raise self.error("TypeError", "object does not support item "
                                          "assignment (every value here is "
                                          "immutable)")

    def lookup(self, name: str, env: Dict):
        if name in env:
            return env[name]
        if name in self.globals:
            return self.globals[name]
        if name in BUILTINS:
            return _Builtin(name)
        raise self.error("NameError", f"name {name!r} is not defined")

    # -- match / case ------------------------------------------------------
    def exec_match(self, s: ast.Match, env: Dict) -> None:
        subject = self.eval(s.subject, env)
        for i, case in enumerate(s.cases):
            binds: Dict[str, object] = {}
            if self.pattern(case.pattern, subject, binds, env):
                env.update(binds)
                if case.guard is None or self.truth(self.eval(case.guard, env)):
                    self.step("control", f"The subject {_m(subject)} takes "
                              f"case {i}.",
                              f"branch({_m(subject)}) = {i}", "True")
                    self.exec_block(case.body, env)
                    return
        self.step("control", f"No case matches {_m(subject)}; nothing runs.",
                  f"branch({_m(subject)}) = none", "True")

    def pattern(self, p: ast.pattern, subject, binds: Dict, env: Dict) -> bool:
        if isinstance(p, ast.MatchValue):
            return self.equal(subject, self.eval(p.value, env))
        if isinstance(p, ast.MatchSingleton):
            return subject is p.value or (
                isinstance(subject, bool) and subject == p.value
                and isinstance(p.value, bool))
        if isinstance(p, ast.MatchAs):
            if p.pattern is not None and not self.pattern(p.pattern, subject,
                                                          binds, env):
                return False
            if p.name is not None:
                binds[p.name] = subject
            return True
        if isinstance(p, ast.MatchOr):
            for alt in p.patterns:
                trial: Dict[str, object] = {}
                if self.pattern(alt, subject, trial, env):
                    binds.update(trial)
                    return True
            return False
        if isinstance(p, ast.MatchSequence):
            if not isinstance(subject, (tuple, range)):
                return False
            items = list(subject)
            stars = [k for k, q in enumerate(p.patterns)
                     if isinstance(q, ast.MatchStar)]
            if not stars:
                if len(items) != len(p.patterns):
                    return False
                return all(self.pattern(q, v, binds, env)
                           for q, v in zip(p.patterns, items))
            k = stars[0]
            after = len(p.patterns) - k - 1
            if len(items) < len(p.patterns) - 1:
                return False
            head, tail = items[:k], items[len(items) - after:]
            if not all(self.pattern(q, v, binds, env)
                       for q, v in zip(p.patterns[:k], head)):
                return False
            if not all(self.pattern(q, v, binds, env)
                       for q, v in zip(p.patterns[k + 1:], tail)):
                return False
            star = p.patterns[k]
            if star.name is not None:
                binds[star.name] = tuple(items[k:len(items) - after])
            return True
        raise PythonRefusal("UNSUPPORTED", f"pattern {type(p).__name__}")

    # -- expressions -------------------------------------------------------
    def eval(self, node: ast.expr, env: Dict):
        if isinstance(node, MUTABLE_NODES):
            raise PythonRefusal("MUTABLE_CONTAINER",
                                f"a {type(node).__name__} is mutable; the "
                                "carrier holds tuples and frozensets")
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, (bool, int, str)) or v is None:
                return v
            raise PythonRefusal("UNSUPPORTED", f"constant {type(v).__name__}")
        if isinstance(node, ast.Name):
            return self.lookup(node.id, env)
        if isinstance(node, ast.Tuple):
            out = tuple(self.eval(e, env) for e in node.elts)
            return self.carrier_tuple(out)
        if isinstance(node, ast.BinOp):
            return self.binop(node.op, self.eval(node.left, env),
                              self.eval(node.right, env))
        if isinstance(node, ast.UnaryOp):
            return self.unary(node.op, self.eval(node.operand, env))
        if isinstance(node, ast.BoolOp):
            is_and = isinstance(node.op, ast.And)
            value = None
            for sub in node.values:
                value = self.eval(sub, env)
                t = self.truth(value)
                if (is_and and not t) or (not is_and and t):
                    break
            self.step("substrate", f"The {'and' if is_and else 'or'} chain "
                      f"settles on {_m(value)}.",
                      f"{'∧' if is_and else '∨'}-chain = {_m(value)}",
                      "True")
            return value
        if isinstance(node, ast.Compare):
            left = self.eval(node.left, env)
            for op, comp in zip(node.ops, node.comparators):
                right = self.eval(comp, env)
                if not self.compare(op, left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            return self.eval(node.body if self.truth(self.eval(node.test, env))
                             else node.orelse, env)
        if isinstance(node, ast.Subscript):
            return self.subscript(self.eval(node.value, env), node.slice, env)
        if isinstance(node, ast.Attribute):
            return self.attribute(self.eval(node.value, env), node.attr)
        if isinstance(node, ast.Call):
            return self.call(node, env)
        if isinstance(node, (ast.Lambda, ast.GeneratorExp, ast.JoinedStr,
                             ast.NamedExpr, ast.Starred, ast.Await,
                             ast.Yield, ast.YieldFrom)):
            raise PythonRefusal("UNSUPPORTED",
                                f"expression {type(node).__name__}")
        raise PythonRefusal("UNSUPPORTED", f"expression {type(node).__name__}")

    def carrier_tuple(self, items: tuple) -> tuple:
        if len(items) > ps.WIDTH:
            raise PythonRefusal("CARRIER_OVERFLOW",
                                f"a tuple of {len(items)} does not fit one "
                                "24-coordinate carrier")
        return items

    # -- truth -------------------------------------------------------------
    def truth(self, v) -> bool:
        if isinstance(v, bool):
            return v
        if _is_num(v):
            return v != 0
        if isinstance(v, (str, tuple, range)):
            return len(v) > 0
        if isinstance(v, frozenset):
            return bool(ps.mask_of_frozenset(v))
        if v is None:
            return False
        if isinstance(v, (_Function, _Builtin)):
            return True
        raise PythonRefusal("UNSUPPORTED", f"the truth of a {_tname(v)}")

    # -- arithmetic --------------------------------------------------------
    def binop(self, op: ast.operator, a, b):
        name = type(op).__name__
        sym = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
               "FloorDiv": "//", "Mod": "%", "Pow": "**", "LShift": "<<",
               "RShift": ">>", "BitAnd": "&", "BitOr": "|", "BitXor": "^",
               "MatMult": "@"}[name]
        expr = f"{literal(a)} {sym} {literal(b)}" if not isinstance(
            a, _Function) and not isinstance(b, _Function) else None
        if isinstance(a, Quantity) or isinstance(b, Quantity):
            return self.quantity_op(name, sym, a, b)
        if name in ("BitAnd", "BitOr", "BitXor") or (
                name == "Sub" and isinstance(a, frozenset)):
            return self.bitwise(name, sym, a, b)
        if name in ("LShift", "RShift"):
            if not (_is_int(a) and _is_int(b)):
                raise self.error("TypeError", f"unsupported operand types "
                                 f"for {sym}: {_tname(a)} and {_tname(b)}")
            if b < 0:
                raise self.error("ValueError", "negative shift count")
            value = ps.dyadic_shift(int(a), int(b), name == "LShift")
            how = (f"{_m(a)} · 2^{b} = {value}" if name == "LShift"
                   else f"⌊{_m(a)} / 2^{b}⌋ = {value}")
            self.step("integer", f"Move {_m(a)} {'up' if name == 'LShift' else 'down'} "
                      f"{b} planes of the dyadic tower.", how,
                      f"same({expr}, {literal(value)})")
            return value
        if isinstance(a, (str, tuple)) or isinstance(b, (str, tuple)):
            return self.sequence_op(name, sym, a, b, expr)
        if not (_is_num(a) and _is_num(b)):
            raise self.error("TypeError", f"unsupported operand types for "
                             f"{sym}: {_tname(a)} and {_tname(b)}")
        if name == "Div":
            if b == 0:
                raise self.error("ZeroDivisionError", "division by zero")
            if not (isinstance(a, Fraction) or isinstance(b, Fraction)):
                self.certificate = (f"isinstance({literal(a)}, int) and "
                                    f"isinstance({literal(b)}, int)")
                raise PythonRefusal(
                    "FLOAT", f"{_m(a)} / {_m(b)}: true division of two ints "
                             "is a float in Python 3; write "
                             f"Fraction({_m(a)}, {_m(b)}) for the exact value")
            if b == 0:
                raise self.error("ZeroDivisionError", "division by zero")
            value = Fraction(a) / Fraction(b)
        elif name in ("FloorDiv", "Mod"):
            if b == 0:
                raise self.error("ZeroDivisionError", "division by zero")
            value = a // b if name == "FloorDiv" else a % b
        elif name == "Pow":
            value = self.power(a, b)
        elif name == "Add":
            value = a + b
        elif name == "Sub":
            value = a - b
        elif name == "Mult":
            value = a * b
        else:
            raise PythonRefusal("UNSUPPORTED", f"operator {sym}")
        layer = "rational" if isinstance(value, Fraction) else "integer"
        field_ = "ℚ" if layer == "rational" else "ℤ"
        self.step(layer, f"Compute {_m(a)} {sym} {_m(b)} exactly on the "
                  f"{layer} layer.", f"{_m(a)} {sym} {_m(b)} = {_m(value)} "
                  f"over {field_}", f"same({expr}, {literal(value)})")
        return value

    def power(self, a, b):
        if a == 0 and b < 0:
            raise self.error("ZeroDivisionError", "0 cannot be raised to a "
                                                  "negative power")
        if isinstance(b, Fraction) and b.denominator != 1:
            raise PythonRefusal("FLOAT", f"{_m(a)} ** {_m(b)}: a fractional "
                                "exponent gives an IEEE-754 (or complex) "
                                "value in Python")
        e = int(b)
        if e < 0 and a == 0:
            raise self.error("ZeroDivisionError", "0 cannot be raised to a "
                                                  "negative power")
        if e < 0 and not isinstance(a, Fraction) and not isinstance(
                b, Fraction):
            self.certificate = (f"isinstance({literal(a)}, int) and "
                                f"{literal(b)} < 0")
            raise PythonRefusal("FLOAT", f"{_m(a)} ** {e}: an int to a "
                                "negative int power is a float in Python; "
                                f"write Fraction({_m(a)}) ** {e}")
        size = max(abs(Fraction(a).numerator).bit_length(),
                   Fraction(a).denominator.bit_length(), 1) * abs(e)
        if size > MAX_POWER_BITS:
            raise PythonRefusal("BUDGET", f"a power of about {size} bits")
        value = a ** b
        if isinstance(value, (float, complex)):     # pragma: no cover
            raise PythonRefusal("FLOAT", "the power left the exact layers")
        return value

    def sequence_op(self, name: str, sym: str, a, b, expr: str):
        if name == "Add" and type(a) is type(b) and isinstance(a, (str, tuple)):
            value = a + b if isinstance(a, str) else self.carrier_tuple(
                tuple(a) + tuple(b))
            self.step("rational", f"Concatenate: the second block follows the "
                      f"first ({len(a)} + {len(b)} positions).",
                      f"|u ⧺ v| = {len(a)} + {len(b)} = {len(value)}",
                      f"same({expr}, {literal(value)})")
            return value
        if name == "Mult":
            seq, n = (a, b) if isinstance(a, (str, tuple)) else (b, a)
            if not (_is_int(n) and isinstance(seq, (str, tuple))):
                raise self.error("TypeError", f"can't multiply sequence by "
                                 f"{_tname(n)}")
            n = max(int(n), 0)
            self.tick(n * len(seq))
            value = seq * n if isinstance(seq, str) else self.carrier_tuple(
                tuple(seq) * n)
            self.step("rational", f"Repeat a block of {len(seq)} positions "
                      f"{n} times.", f"|u^{n}| = {n} · {len(seq)} = "
                      f"{len(value)}", f"same({expr}, {literal(value)})")
            return value
        if name == "Mod" and isinstance(a, str):
            raise PythonRefusal("UNSUPPORTED", "string formatting")
        raise self.error("TypeError", f"unsupported operand types for {sym}: "
                         f"{_tname(a)} and {_tname(b)}")

    def quantity_op(self, name: str, sym: str, a, b):
        if name not in ("Add", "Sub"):
            raise self.error("TypeError", f"unsupported operand types for "
                             f"{sym}: {_tname(a)} and {_tname(b)}")
        self.same_scale(a, b)
        value = Quantity(a.value + b.value if name == "Add"
                         else a.value - b.value, a.name)
        self.step("rational", f"Add on one declared scale ({a.name}).",
                  f"{_m(a.value)} {a.name} {sym} {_m(b.value)} {a.name} = "
                  f"{_m(value.value)} {a.name}",
                  f"same({literal(a)} {sym} {literal(b)}, {literal(value)})")
        return value

    def same_scale(self, a, b) -> None:
        if not (isinstance(a, Quantity) and isinstance(b, Quantity)):
            raise PythonRefusal("SCALE_MISMATCH", "a quantity meets a bare "
                                "number, whose scale is undeclared")
        if a.name != b.name:
            raise PythonRefusal("SCALE_MISMATCH", f"{a.name} against "
                                f"{b.name}: the scales are not converted "
                                "silently")

    # -- the sub-registers ---------------------------------------------------
    def bitwise(self, name: str, sym: str, a, b):
        prog = {"BitAnd": "and", "BitOr": "or", "BitXor": "xor",
                "Sub": "andnot"}[name]
        if isinstance(a, frozenset) and isinstance(b, frozenset):
            ma, mb = ps.mask_of_frozenset(a), ps.mask_of_frozenset(b)
            run = ps.register_bitwise(prog, ma, mb)
            value = ps.frozenset_of_mask(run.value)
            setop = {"and": "∩", "or": "∪", "xor": "Δ", "andnot": "∖"}[prog]
            self.step("substrate", f"Set {setop} as mask algebra: the "
                      f"{prog.upper()} program on {run.lanes} register lanes, "
                      f"undone lane by lane with 0 bits erased.",
                      f"{ma:#026b} {sym} {mb:#026b} = {run.value:#026b} over "
                      f"F₂^24 ({run.gate_count} gates)",
                      f"same({literal(a)} {sym} {literal(b)}, "
                      f"{literal(value)})")
            return value
        if name == "Sub":                           # pragma: no cover
            raise self.error("TypeError", "unsupported operand types for -")
        if not (_is_int(a) and _is_int(b)):
            raise self.error("TypeError", f"unsupported operand types for "
                             f"{sym}: {_tname(a)} and {_tname(b)}")
        run = ps.register_bitwise(prog, int(a), int(b))
        value = run.value
        if isinstance(a, bool) and isinstance(b, bool):
            value = bool(value)
        self.step("substrate", f"{prog.upper()} on the sub-registers: "
                  f"{run.carriers} carrier(s) × 8 registers × 3 lanes in two's "
                  f"complement; the inverse program restored every lane.",
                  f"{_m(a)} {sym} {_m(b)} = {_m(value)} over F₂^{run.width} "
                  f"({run.gate_count} gates, {run.erased_bits} bits erased)",
                  f"same({literal(a)} {sym} {literal(b)}, {literal(value)})")
        return value

    def unary(self, op: ast.unaryop, v):
        if isinstance(op, ast.Not):
            value = not self.truth(v)
            self.step("substrate", f"Negate the truth bit of {_m(v)}.",
                      f"¬{1 if not value else 0} = {1 if value else 0} in F₂",
                      f"same(not {literal(v)}, {literal(value)})")
            return value
        if isinstance(op, ast.Invert):
            if not _is_int(v):
                raise self.error("TypeError", f"bad operand type for unary ~: "
                                 f"{_tname(v)}")
            run = ps.register_invert(int(v))
            self.step("substrate", f"NOT on every lane of the register tower "
                      f"({run.carriers} carrier(s)).",
                      f"~{_m(v)} = -{_m(v)} - 1 = {run.value} "
                      f"({run.gate_count} gates)",
                      f"same(~{literal(v)}, {literal(run.value)})")
            return run.value
        if not _is_num(v):
            if isinstance(v, Quantity):
                raise self.error("TypeError", "bad operand type for unary "
                                              "operator: unit")
            raise self.error("TypeError", f"bad operand type for unary "
                             f"operator: {_tname(v)}")
        value = -v if isinstance(op, ast.USub) else +v
        sym = "-" if isinstance(op, ast.USub) else "+"
        self.step("rational" if isinstance(value, Fraction) else "integer",
                  f"Reflect {_m(v)} through 0." if sym == "-" else
                  f"Keep {_m(v)}.", f"{sym}({_m(v)}) = {_m(value)}",
                  f"same({sym}({literal(v)}), {literal(value)})")
        return value

    # -- comparison ----------------------------------------------------------
    def equal(self, a, b) -> bool:
        if isinstance(a, Quantity) or isinstance(b, Quantity):
            self.same_scale(a, b)
            return a.value == b.value
        if _is_num(a) and _is_num(b):
            return (a - b) == 0
        if isinstance(a, str) and isinstance(b, str):
            return len(a) == len(b) and all(ord(x) == ord(y)
                                            for x, y in zip(a, b))
        if isinstance(a, tuple) and isinstance(b, tuple):
            return len(a) == len(b) and all(self.equal(x, y)
                                            for x, y in zip(a, b))
        if isinstance(a, frozenset) and isinstance(b, frozenset):
            return ps.mask_of_frozenset(a) == ps.mask_of_frozenset(b)
        if isinstance(a, range) and isinstance(b, range):
            return a == b
        if a is None or b is None:
            return a is b
        return False

    def order(self, a, b) -> int:
        if isinstance(a, Quantity) or isinstance(b, Quantity):
            self.same_scale(a, b)
            a, b = a.value, b.value
        if _is_num(a) and _is_num(b):
            d = a - b
            return (d > 0) - (d < 0)
        if isinstance(a, str) and isinstance(b, str):
            for x, y in zip(a, b):
                if ord(x) != ord(y):
                    return 1 if ord(x) > ord(y) else -1
            return (len(a) > len(b)) - (len(a) < len(b))
        if isinstance(a, tuple) and isinstance(b, tuple):
            for x, y in zip(a, b):
                if not self.equal(x, y):
                    return self.order(x, y)
            return (len(a) > len(b)) - (len(a) < len(b))
        raise self.error("TypeError", f"'<' not supported between "
                         f"{_tname(a)} and {_tname(b)}")

    def compare(self, op: ast.cmpop, a, b) -> bool:
        name = type(op).__name__
        sym = {"Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=", "Gt": ">",
               "GtE": ">=", "In": "in", "NotIn": "not in", "Is": "is",
               "IsNot": "is not"}[name]
        if name in ("Eq", "NotEq"):
            value = self.equal(a, b) == (name == "Eq")
            how = "coordinate displacement a − b"
        elif name in ("In", "NotIn"):
            value = self.contains(b, a) == (name == "In")
            how = "membership"
        elif name in ("Is", "IsNot"):
            if not (b is None or isinstance(b, bool)):
                raise PythonRefusal("UNSUPPORTED", "identity beyond None, "
                                                   "True and False")
            value = ((a is b) or (isinstance(a, bool) and isinstance(b, bool)
                                  and a == b)) == (name == "Is")
            how = "identity"
        elif isinstance(a, frozenset) and isinstance(b, frozenset):
            ma, mb = ps.mask_of_frozenset(a), ps.mask_of_frozenset(b)
            sub, sup = ma & ~mb == 0, mb & ~ma == 0
            value = {"LtE": sub, "Lt": sub and ma != mb, "GtE": sup,
                     "Gt": sup and ma != mb}[name]
            how = "mask containment"
        else:
            s = self.order(a, b)
            value = {"Lt": s < 0, "LtE": s <= 0, "Gt": s > 0,
                     "GtE": s >= 0}[name]
            how = f"sign(a − b) = {s}"
        self.step("rational", f"Compare {_m(a)} {sym} {_m(b)}: "
                  f"{'true' if value else 'false'} ({how}).",
                  f"[{_m(a)} {sym} {_m(b)}] = {1 if value else 0}",
                  f"same(({literal(a)} {sym} {literal(b)}), {value!r})")
        return value

    def contains(self, container, item) -> bool:
        if isinstance(container, str):
            if not isinstance(item, str):
                raise self.error("TypeError", "'in <string>' requires string "
                                              "as left operand")
            n, m = len(container), len(item)
            self.tick(max(n - m + 1, 1))
            return any(container[i:i + m] == item for i in range(n - m + 1))
        if isinstance(container, tuple):
            return any(self.equal(item, x) for x in container)
        if isinstance(container, frozenset):
            if _is_num(item) and Fraction(item).denominator == 1 \
                    and 0 <= int(item) < ps.WIDTH:
                return bool(ps.mask_of_frozenset(container) >> int(item) & 1)
            if isinstance(item, Quantity):
                raise self.error("TypeError", "unhashable type: 'unit'")
            return False
        if isinstance(container, range):
            if not _is_num(item) or Fraction(item).denominator != 1:
                return False
            k = int(item)
            r = container
            if r.step > 0 and not r.start <= k < r.stop:
                return False
            if r.step < 0 and not r.stop < k <= r.start:
                return False
            return (k - r.start) % r.step == 0
        raise self.error("TypeError", f"argument of type {_tname(container)} "
                                      "is not iterable")

    def iterate(self, v):
        if isinstance(v, (tuple, str, range)):
            self.tick(0)
            return v
        if isinstance(v, frozenset):
            raise PythonRefusal("ORDER_UNDEFINED", "CPython does not promise "
                                "an iteration order for a set; sort it into "
                                "a tuple first")
        raise self.error("TypeError", f"{_tname(v)} object is not iterable")

    # -- subscripts ------------------------------------------------------------
    def subscript(self, v, s: ast.expr, env: Dict):
        if isinstance(s, ast.Slice):
            parts = []
            for p in (s.lower, s.upper, s.step):
                x = None if p is None else self.eval(p, env)
                if x is not None and not _is_int(x):
                    raise self.error("TypeError", "slice indices must be "
                                                  "integers or None")
                parts.append(None if x is None else int(x))
            if isinstance(v, range):
                value = v[slice(*parts)]
                self.step("integer", "Slice a tick generator.",
                          f"range slice = {literal(value)}",
                          f"same({literal(v)}[{self._sl(parts)}], "
                          f"{literal(value)})")
                return value
            if not isinstance(v, (str, tuple)):
                raise self.error("TypeError", f"{_tname(v)} object is not "
                                              "subscriptable")
            idx = ps.slice_indices(len(v), *parts)
            self.tick(len(idx))
            value = "".join(v[i] for i in idx) if isinstance(v, str) else \
                tuple(v[i] for i in idx)
            start = idx[0] if idx else "∅"
            step = 1 if parts[2] is None else parts[2]
            cells = ", ".join("c%d(%d,%d)" % ps.cell_of_position(i)
                              for i in idx[:6])
            more = ", …" if len(idx) > 6 else ""
            self.step("rational", f"Slice as a coordinate map: read "
                      f"{len(idx)} positions, starting at {start} with step "
                      f"{step}, after clamping to the {len(v)} positions "
                      f"held.",
                      f"i ↦ {start} + {step}·i for i < {len(idx)}: positions "
                      f"{list(idx[:12])}{more}; MOG cells {cells}{more}",
                      f"same({literal(v)}[{self._sl(parts)}], "
                      f"{literal(value)})")
            return value
        i = self.eval(s, env)
        if isinstance(v, (str, tuple, range)):
            if not _is_int(i):
                raise self.error("TypeError", "indices must be integers")
            n = len(v)
            k = int(i) + n if i < 0 else int(i)
            if not 0 <= k < n:
                raise self.error("IndexError", "index out of range")
            value = (v.start + k * v.step) if isinstance(v, range) else v[k]
            where = ("x_k = %d + %d·%d" % (v.start, k, v.step)
                     if isinstance(v, range) else
                     "position %d = carrier %d, MOG cell (%d, %d)"
                     % ((k,) + ps.cell_of_position(k)))
            self.step("integer", f"Read position {k} of {n}.",
                      f"{where} ↦ {_m(value)}",
                      f"same({literal(v)}[{literal(i)}], {literal(value)})")
            return value
        raise self.error("TypeError", f"{_tname(v)} object is not "
                                      "subscriptable")

    @staticmethod
    def _sl(parts) -> str:
        return ":".join("" if p is None else str(p) for p in parts)

    def attribute(self, v, attr: str):
        if isinstance(v, _Module) and attr == "Fraction":
            return _Builtin("Fraction")
        if _is_num(v) and attr in ("numerator", "denominator"):
            f = Fraction(v)
            value = f.numerator if attr == "numerator" else f.denominator
            self.step("rational", f"Read the {attr} of {_m(v)} in lowest "
                      "terms.", f"{_m(v)} = p/q, gcd(p, q) = 1, q > 0 ⇒ "
                      f"{attr} = {value}",
                      f"same(({literal(v)}).{attr}, {value})")
            return value
        if _is_int(v) and attr in ("bit_length", "bit_count"):
            return _Method(attr, int(v))
        raise PythonRefusal("UNSUPPORTED", f"attribute .{attr} of a "
                                           f"{_tname(v)}")

    # -- calls -----------------------------------------------------------------
    def call(self, node: ast.Call, env: Dict):
        if node.keywords or any(isinstance(a, ast.Starred) for a in node.args):
            raise PythonRefusal("UNSUPPORTED", "keyword or starred arguments")
        f = self.eval(node.func, env)
        if isinstance(f, _Method):
            attr, n = f.attr, f.receiver
            if node.args:
                raise self.error("TypeError", f"{attr}() takes no arguments")
            if attr == "bit_length":
                value = abs(n).bit_length()
                math = f"⌈log₂(|{n}| + 1)⌉ = {value}"
            else:
                value = bin(ps.register_load(abs(n) % (1 << 24)).value).count(
                    "1") if abs(n) < (1 << 24) else bin(abs(n)).count("1")
                math = f"popcount(|{n}|) = {value} (Hamming weight on F₂)"
            self.step("integer", f"The {attr} of {n}.", math,
                      f"same(({n}).{attr}(), {value})")
            return value
        if (isinstance(node.func, ast.Name) and node.func.id == "frozenset"
                and f == _Builtin("frozenset") and len(node.args) == 1
                and isinstance(node.args[0], ast.Set)):
            items = [self.eval(e, env) for e in node.args[0].elts]
            return self.make_frozenset(items)
        args = [self.eval(a, env) for a in node.args]
        if isinstance(f, _Function):
            return self.call_function(f, args)
        if isinstance(f, _Builtin):
            return getattr(self, "b_" + f.name)(*args)
        raise self.error("TypeError", f"{_tname(f)} object is not callable")

    def call_function(self, f: _Function, args: List):
        if len(args) != len(f.params):
            raise self.error("TypeError", f"{f.name}() takes "
                             f"{len(f.params)} arguments, {len(args)} given")
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise PythonRefusal("BUDGET", f"recursion deeper than {MAX_DEPTH}")
        local: Dict[str, object] = dict(zip(f.params, args))
        try:
            self.exec_block(f.body, local)
            value = None
        except _Return as r:
            value = r.value
        finally:
            self.depth -= 1
        return value

    def make_frozenset(self, items) -> frozenset:
        mask = ps.mask_of_frozenset(items)
        value = ps.frozenset_of_mask(mask)
        self.step("substrate", f"Lay the set on the 24 coordinates as a "
                  f"mask of weight {len(value)}.",
                  f"mask = {mask:#026b}, wt = {len(value)}",
                  f"same(frozenset({literal(tuple(items))}), "
                  f"{literal(value)})")
        return value

    # -- the builtins, one method each -------------------------------------------
    def _need(self, args, lo, hi, name):
        if not lo <= len(args) <= hi:
            raise self.error("TypeError", f"{name}() takes {lo}..{hi} "
                                          f"arguments, {len(args)} given")

    def b_len(self, *args):
        self._need(args, 1, 1, "len")
        v = args[0]
        if isinstance(v, frozenset):
            value = len(ps.frozenset_of_mask(ps.mask_of_frozenset(v)))
            math = f"wt(mask) = {value}"
        elif isinstance(v, (str, tuple, range)):
            value = len(v)
            math = f"|v| = {value}"
        else:
            raise self.error("TypeError", f"object of type {_tname(v)} has "
                                          "no len()")
        self.step("integer", f"Count the positions held: {value}.", math,
                  f"same(len({literal(v)}), {value})")
        return value

    def b_abs(self, *args):
        self._need(args, 1, 1, "abs")
        v = args[0]
        if not _is_num(v):
            raise self.error("TypeError", f"bad operand type for abs(): "
                                          f"{_tname(v)}")
        value = abs(v)
        self.step("rational", f"Distance of {_m(v)} from 0.",
                  f"|{_m(v)}| = {_m(value)}",
                  f"same(abs({literal(v)}), {literal(value)})")
        return value

    def b_sum(self, *args):
        self._need(args, 1, 2, "sum")
        seq, start = args[0], (args[1] if len(args) == 2 else 0)
        if isinstance(seq, range):
            n = len(seq)
            self.tick(n)
            if not _is_num(start):
                raise self.error("TypeError", "sum() start must be a number")
            value = start + (n * (2 * seq.start + (n - 1) * seq.step)) // 2 \
                if n else start
            self.step("integer", f"Sum {n} ticks of the generator "
                      f"x_k = {seq.start} + {seq.step}k in closed form "
                      f"({n} steps of cost).",
                      f"Σ_(k<{n}) ({seq.start} + {seq.step}k) = {n}·(2·"
                      f"{seq.start} + {n - 1}·{seq.step})/2 = {_m(value)}",
                      f"same(sum({literal(seq)}, {literal(start)}), "
                      f"{literal(value)})")
            return value
        items = list(self.iterate(seq))
        if isinstance(seq, str):
            raise self.error("TypeError", "sum() can't sum strings")
        value = start
        for x in items:
            self.tick()
            if not (_is_num(x) and _is_num(value)):
                raise self.error("TypeError", f"unsupported operand types "
                                 f"for +: {_tname(value)} and {_tname(x)}")
            value = value + x
        self.step("rational" if isinstance(value, Fraction) else "integer",
                  f"Accumulate {len(items)} exact terms.",
                  " + ".join(_m(x) for x in items[:12])
                  + (" + …" if len(items) > 12 else "") + f" = {_m(value)}",
                  f"same(sum({literal(seq)}, {literal(start)}), "
                  f"{literal(value)})")
        return value

    def _extremum(self, args, sign: int, name: str):
        if not args:
            raise self.error("TypeError", f"{name} expected an argument")
        items = list(self.iterate(args[0])) if len(args) == 1 else list(args)
        if not items:
            raise self.error("ValueError", f"{name}() arg is an empty "
                                           "sequence")
        best = items[0]
        for x in items[1:]:
            self.tick()
            if self.order(x, best) * sign > 0:
                best = x
        call = ", ".join(literal(a) for a in args)
        self.step("rational", f"The {name} of {len(items)} values by exact "
                  "comparison.", f"{name}{{{', '.join(_m(x) for x in items[:8])}"
                  f"}} = {_m(best)}", f"same({name}({call}), {literal(best)})")
        return best

    def b_max(self, *args):
        return self._extremum(args, 1, "max")

    def b_min(self, *args):
        return self._extremum(args, -1, "min")

    def b_divmod(self, *args):
        self._need(args, 2, 2, "divmod")
        a, b = args
        if not (_is_num(a) and _is_num(b)):
            raise self.error("TypeError", "unsupported operand types for "
                                          "divmod()")
        if b == 0:
            raise self.error("ZeroDivisionError", "integer division or "
                                                  "modulo by zero")
        value = (a // b, a % b)
        self.step("integer", f"Divide {_m(a)} by {_m(b)} with the floor "
                  "convention.", f"{_m(a)} = {_m(b)}·{_m(value[0])} + "
                  f"{_m(value[1])}", f"same(divmod({literal(a)}, "
                  f"{literal(b)}), {literal(value)})")
        return value

    def b_pow(self, *args):
        self._need(args, 2, 3, "pow")
        if len(args) == 2:
            return self.binop(ast.Pow(), args[0], args[1])
        a, b, m = args
        if not all(_is_int(x) for x in args):
            raise self.error("TypeError", "pow() 3rd argument not allowed "
                                          "unless all arguments are integers")
        if m == 0:
            raise self.error("ValueError", "pow() 3rd argument cannot be 0")
        try:
            value = pow(int(a), int(b), int(m))
        except ValueError as exc:
            raise self.error("ValueError", str(exc))
        self.step("integer", f"Modular power by repeated squaring, mod "
                  f"{m}.", f"{a}^{b} ≡ {value} (mod {m})",
                  f"same(pow({a}, {b}, {m}), {value})")
        return value

    def b_ord(self, *args):
        self._need(args, 1, 1, "ord")
        c = args[0]
        if not isinstance(c, str) or len(c) != 1:
            raise self.error("TypeError", "ord() expected a character")
        run = ps.register_load(ord(c))
        self.step("substrate", f"Load the code point of {c!r} into one "
                  "24-bit word through the COPY program.",
                  f"ord({c!r}) = {run.value} = {run.value:#026b}",
                  f"same(ord({c!r}), {run.value})")
        return run.value

    def b_chr(self, *args):
        self._need(args, 1, 1, "chr")
        n = args[0]
        if not _is_int(n):
            raise self.error("TypeError", "an integer is required")
        if not 0 <= n <= 0x10FFFF:
            raise self.error("ValueError", "chr() arg not in range(0x110000)")
        run = ps.register_load(int(n))
        value = chr(run.value)
        self.step("substrate", f"Read the 24-bit word {run.value} back as a "
                  "character.", f"chr({run.value}) = {value!r}",
                  f"same(chr({int(n)}), {value!r})")
        return value

    def b_tuple(self, *args):
        self._need(args, 0, 1, "tuple")
        if not args:
            return ()
        items = self.iterate(args[0])
        self.tick(len(items))
        if len(items) > ps.WIDTH:
            raise PythonRefusal("CARRIER_OVERFLOW", f"{len(items)} items do "
                                "not fit one 24-coordinate carrier")
        value = tuple(items)
        self.step("rational", f"Align {len(value)} values on the carrier "
                  "coordinates, in order.", f"(q_0 … q_{max(len(value)-1, 0)})"
                  f" = {literal(value)}",
                  f"same(tuple({literal(args[0])}), {literal(value)})")
        return value

    def b_frozenset(self, *args):
        self._need(args, 0, 1, "frozenset")
        if not args:
            return frozenset()
        if isinstance(args[0], frozenset):
            return args[0]
        return self.make_frozenset(list(self.iterate(args[0])))

    def b_range(self, *args):
        self._need(args, 1, 3, "range")
        if not all(_is_int(a) for a in args):
            raise self.error("TypeError", "range() takes integers")
        if len(args) == 3 and args[2] == 0:
            raise self.error("ValueError", "range() arg 3 must not be zero")
        return range(*[int(a) for a in args])

    def b_Fraction(self, *args):
        self._need(args, 1, 2, "Fraction")
        for a in args:
            if not (_is_num(a) or (isinstance(a, str) and len(args) == 1)):
                raise self.error("TypeError", "Fraction() takes rationals "
                                              "or one string")
        try:
            value = Fraction(*args)
        except ZeroDivisionError as exc:
            raise self.error("ZeroDivisionError", str(exc))
        except ValueError as exc:
            raise self.error("ValueError", str(exc))
        call = ", ".join(literal(a) for a in args)
        self.step("rational", f"Place {_m(value)} on a carrier coordinate, "
                  "in lowest terms with a positive denominator.",
                  f"q = {_m(value)}, gcd = 1", f"same(Fraction({call}), "
                  f"{literal(value)})")
        return value

    def b_int(self, *args):
        self._need(args, 0, 1, "int")
        if not args:
            return 0
        v = args[0]
        if _is_num(v):
            value = int(v)
        elif isinstance(v, str):
            try:
                value = int(v)
            except ValueError as exc:
                raise self.error("ValueError", str(exc))
        else:
            raise self.error("TypeError", f"int() can't convert {_tname(v)}")
        self.step("integer", f"The integer reading of {_m(v)} (truncation "
                  "towards 0).", f"int({_m(v)}) = {value}",
                  f"same(int({literal(v)}), {value})")
        return value

    def b_bool(self, *args):
        self._need(args, 0, 1, "bool")
        value = self.truth(args[0]) if args else False
        self.step("substrate", "Read the truth bit.",
                  f"bool = {1 if value else 0} in F₂",
                  f"same(bool({literal(args[0]) if args else ''}), {value!r})")
        return value

    def b_unit(self, *args):
        self._need(args, 2, 2, "unit")
        v, name = args
        if isinstance(v, bool) or not _is_num(v) or not isinstance(name, str):
            raise PythonRefusal("FLOAT", "a unit value must be exact")
        return Quantity(v, name)

    def _mask_arg(self, x) -> int:
        if isinstance(x, frozenset):
            return ps.mask_of_frozenset(x)
        if isinstance(x, int) and not isinstance(x, bool) \
                and 0 <= x < 1 << ps.WIDTH:
            return x
        raise PythonRefusal("OUTSIDE_SUBSTRATE", f"{_m(x)} is not a 24-bit "
                                                 "mask")

    def b_golay_encode(self, *args):
        self._need(args, 1, 1, "golay_encode")
        value = ps.golay_encode(args[0])
        self.step("substrate", f"Encode the 12-bit message {args[0]} as a "
                  "Golay codeword.", f"m·G = {value:#026b}",
                  f"same(golay_encode({args[0]}), {value})")
        return value

    def b_hamming(self, *args):
        self._need(args, 2, 2, "hamming")
        a, b = (self._mask_arg(x) for x in args)
        run = ps.register_bitwise("xor", a, b)
        value = bin(run.value).count("1")
        self.step("substrate", "Hamming distance: XOR on the registers, "
                  "then count the set lanes.",
                  f"d_H = wt({a:#x} ⊕ {b:#x}) = {value}",
                  f"same(hamming({literal(args[0])}, {literal(args[1])}), "
                  f"{value})")
        return value

    def b_classify(self, *args):
        if len(args) < 2:
            raise self.error("TypeError", "classify() needs a subject and at "
                                          "least one case")
        subject = self._mask_arg(args[0])
        cases = [self._mask_arg(c) for c in args[1:]]
        c = ps.classify(subject, cases)
        call = ", ".join(str(x) for x in [subject] + cases)
        dist = list(c.distances)
        if c.verdict == "branch":
            self.step("substrate", f"Coset-decode the subject: weight "
                      f"{c.coset_weight}, inside the packing radius, so the "
                      f"declared case {c.branch} is the unique nearest.",
                      f"d_H(s, c_i) = {dist}; min = {min(dist)} ≤ 3 ⇒ branch "
                      f"{c.branch} (balls of radius 3 around codewords are "
                      "disjoint: minimum distance 8)",
                      f"same(classify({call}), {c.branch})")
            return c.branch
        if c.verdict == "AMBIGUOUS":
            self.certificate = (
                f"sum(1 for m in range(4096) if hamming({subject}, "
                f"golay_encode(m)) == 4) == 6 and min(hamming({subject}, "
                f"golay_encode(m)) for m in range(4096)) == 4 and "
                f"min(hamming({subject}, c) for c in {cases}) == 4")
            raise PythonRefusal(
                "AMBIGUOUS", f"the subject lies in a deep hole: coset weight "
                f"4, six equidistant codewords, nearest declared case at "
                f"distance 4 (distances {dist})")
        self.certificate = f"min(hamming({subject}, c) for c in {cases}) >= 5"
        raise PythonRefusal(
            "UNCORRECTABLE", f"the nearest declared case is at distance "
            f"{min(dist)} ≥ 5 (distances {dist}); the decoder's own codeword "
            "is not a declared case")

    # -- the carried fork (studies/CARRIED_FORK_STUDY.md) ---------------------
    def _fork_refusal(self, r, what: str, certificate: str):
        live = ", ".join(f"{c:#x}" for c in r.live)
        self.certificate = certificate
        if r.verdict == "AMBIGUOUS":
            raise PythonRefusal(
                "AMBIGUOUS", f"the carried fork stays open after {what}: "
                f"{len(r.live)} of {len(r.candidates)} candidates survive "
                f"({live})")
        raise PythonRefusal(
            "UNCORRECTABLE", f"no candidate of the carried fork survives "
            f"{what}")

    def b_nearest(self, *args):
        self._need(args, 1, 1, "nearest")
        subject = self._mask_arg(args[0])
        value = ps.nearest(subject)
        d = bin(subject ^ value[0]).count("1")
        self.step("substrate", f"Carry every nearest codeword of the read: "
                  f"coset weight {d}, {len(value)} candidate(s)"
                  + (" -- the six codewords of a deep hole, one per tetrad "
                     "of its sextet, none chosen" if len(value) == 6 else "")
                  + ".", f"N(s) = {{c ∈ G24 : d_H(s, c) = {d}}}, |N(s)| = "
                  f"{len(value)}", f"same(nearest({subject}), {value!r})")
        return self.carrier_tuple(value)

    def b_resolve(self, *args):
        if len(args) < 2:
            raise self.error("TypeError", "resolve() needs a subject and at "
                                          "least one case")
        subject = self._mask_arg(args[0])
        cases = [self._mask_arg(c) for c in args[1:]]
        r = ps.resolve(subject, cases)
        call = ", ".join(str(x) for x in [subject] + cases)
        if r.verdict == "resolved":
            gone = len(r.candidates) - len(r.live)
            basis = ("inside the packing radius, the decoder's own answer"
                     if r.coset_weight <= 3 else
                     f"a deep hole: {gone} of the six candidates are not "
                     "declared cases and are pruned, under the closed-world "
                     "assumption that the subject is a read of a declared "
                     "case")
            self.step("substrate", f"Carry the fork of the read (coset weight "
                      f"{r.coset_weight}) and prune it to the declared cases: "
                      f"{basis}. Case {r.index} survives alone.",
                      f"N(s) ∩ cases = {{{r.value:#x}}} ⇒ case {r.index}",
                      f"same(resolve({call}), {r.index})")
            return r.index
        self._fork_refusal(r, "the declared cases",
                           f"len([c for c in nearest({subject}) if c in "
                           f"{cases}]) == {len(r.live)}")

    def b_agree(self, *args):
        if not args:
            raise self.error("TypeError", "agree() needs at least one read")
        reads = [self._mask_arg(x) for x in args]
        r = ps.agree(reads)
        call = ", ".join(str(x) for x in reads)
        if r.verdict == "resolved":
            self.step("substrate", f"Carry the fork of each of the "
                      f"{len(reads)} read(s) of one carrier and keep only the "
                      "codewords every read allows (the second-reading "
                      "stage): one survives, and since the carrier lies in "
                      "every fork it is the carrier.",
                      f"⋂ N(r_i) = {{{r.value:#x}}}",
                      f"same(agree({call}), {r.value})")
            return r.value
        self._fork_refusal(r, "every read",
                           f"len(set.intersection(*[set(nearest(r)) for r in "
                           f"{reads}])) == {len(r.live)}")

    def b_resolve_unsure(self, *args):
        self._need(args, 2, 2, "resolve_unsure")
        subject, unsure = (self._mask_arg(x) for x in args)
        r = ps.resolve_unsure(subject, unsure)
        if r.verdict == "resolved":
            self.step("substrate", "Carry the fork of the read and prove "
                      "incorrect every candidate whose error pattern touches "
                      "a coordinate the reader marked sure (errors fall only "
                      "on unsure coordinates); one survives.",
                      f"{{c ∈ N(s) : (s ⊕ c) ⊆ U}} = {{{r.value:#x}}}",
                      f"same(resolve_unsure({subject}, {unsure}), {r.value})")
            return r.value
        self._fork_refusal(r, "the sure coordinates",
                           f"len([c for c in nearest({subject}) if not "
                           f"({subject} ^ c) & (0xFFFFFF & ~{unsure})]) == "
                           f"{len(r.live)}")

    def _rate_arg(self, x, name: str) -> Fraction:
        if not _is_num(x) or isinstance(x, bool):
            raise self.error("TypeError", f"{name}() takes an exact "
                                          "rational bit-flip rate first")
        return Fraction(x)

    def b_decode_confidence(self, *args):
        if len(args) < 2:
            raise self.error("TypeError", "decode_confidence() needs a rate "
                                          "and a subject")
        rate = self._rate_arg(args[0], "decode_confidence")
        subject = self._mask_arg(args[1])
        cases = [self._mask_arg(c) for c in args[2:]]
        r = ps.decode_confidence(rate, subject, cases)
        call = ", ".join([literal(rate)] + [str(x) for x in [subject] + cases])
        conf = r["confidence"]
        if r["reading"] == "decoder":
            language = (f"Decode the read (coset weight {r['coset_weight']}) "
                        f"and weigh every error its coset holds at bit-flip "
                        f"rate {rate}: the decoded codeword is the one sent "
                        f"with probability {_decimal7(conf)}.")
            math = (f"P(c | s) = p^{r['coset_weight']} q^{24 - r['coset_weight']}"
                    f" / Σ_w A_w p^w q^(24−w) = {conf}")
        else:
            language = (f"Carry the fork of the read (coset weight "
                        f"{r['coset_weight']}), prune it to the "
                        f"{r['allowed']} declared case(s) under the "
                        f"closed-world assumption, and weigh every case at "
                        f"bit-flip rate {rate}: case {r['index']} is the one "
                        f"sent with probability {_decimal7(conf)} (at least "
                        f"{_decimal7(r['bound'])}, its rivals lying "
                        f"{r['gap']} or more further away)."
                        if r["gap"] is not None else
                        f"Carry the fork of the read and prune it to the one "
                        f"declared case under the closed-world assumption: "
                        f"with no rival, its probability is 1.")
            math = (f"P(c | s, cases) = p^d(s,c) q^(24−d(s,c)) / Σ_cases "
                    f"p^d q^(24−d) = {conf}")
        self.step("substrate", language, math,
                  f"same(decode_confidence({call}), {literal(conf)})")
        return conf

    def b_agree_confidence(self, *args):
        if len(args) < 2:
            raise self.error("TypeError", "agree_confidence() needs a rate "
                                          "and at least one read")
        rate = self._rate_arg(args[0], "agree_confidence")
        reads = [self._mask_arg(x) for x in args[1:]]
        r = ps.agree_confidence(rate, reads)
        call = ", ".join([literal(rate)] + [str(x) for x in reads])
        conf = r["confidence"]
        self.step("substrate", f"Keep the codewords every one of the "
                  f"{len(reads)} read(s) allows, and weigh every codeword by "
                  f"the product of the reads' likelihoods at bit-flip rate "
                  f"{rate}: the agreed codeword {r['value']:#x} is the "
                  f"carrier with probability {_decimal7(conf)}.",
                  f"P(c | r₁..r_m) = Π_i p^d(r_i,c) q^(24−d(r_i,c)) / Σ_c' "
                  f"Π_i p^d(r_i,c') q^(24−d(r_i,c')) = {conf}",
                  f"same(agree_confidence({call}), {literal(conf)})")
        return conf

    # -- the confidence floor (studies/CONFIDENCE_FLOOR_STUDY.md) ------------
    def _resolve_language(self, r, rate) -> Tuple[str, str]:
        conf = r["confidence"]
        if r["gap"] is None:
            said = ("with no rival declared, it is the one sent with "
                    "probability 1")
        else:
            said = (f"at bit-flip rate {rate} it is the one sent with "
                    f"probability {_decimal7(conf)} — {r['band']} — its "
                    f"rivals lying {r['gap']} or more further away")
        language = (f"Carry the fork of the read (coset weight "
                    f"{r['coset_weight']}), prune it to the {r['allowed']} "
                    f"declared case(s) under the closed-world assumption: "
                    f"case {r['index']} survives alone, and {said}.")
        math = (f"N(s) ∩ cases = {{{r['value']:#x}}} ⇒ case {r['index']}; "
                f"P(c | s, cases) = p^d(s,c) q^(24−d(s,c)) / Σ_cases "
                f"p^d q^(24−d) = {conf}")
        return language, math

    def _agree_language(self, r, reads, rate) -> Tuple[str, str]:
        conf = r["confidence"]
        language = (f"Carry the fork of each of the {len(reads)} read(s) of "
                    f"one carrier and keep only the codewords every read "
                    f"allows: {r['value']:#x} survives alone, and at "
                    f"bit-flip rate {rate} it is the carrier with "
                    f"probability {_decimal7(conf)} — {r['band']}.")
        math = (f"⋂ N(r_i) = {{{r['value']:#x}}}; P(c | r₁..r_m) = "
                f"Π_i p^d(r_i,c) q^(24−d(r_i,c)) / Σ_c' Π_i p^d(r_i,c') "
                f"q^(24−d(r_i,c')) = {conf}")
        return language, math

    def _floor_refusal(self, exc: PythonRefusal, check: str):
        if exc.name == "BELOW_FLOOR":
            self.certificate = check
        raise exc

    def b_resolve_at(self, *args):
        if len(args) < 3:
            raise self.error("TypeError", "resolve_at() needs a rate, a "
                                          "subject and at least one case")
        rate = self._rate_arg(args[0], "resolve_at")
        subject = self._mask_arg(args[1])
        cases = [self._mask_arg(c) for c in args[2:]]
        r = ps.resolve_at(rate, subject, cases)
        call = ", ".join([literal(rate)] + [str(x) for x in [subject] + cases])
        language, math = self._resolve_language(r, rate)
        self.step("substrate", language, math,
                  f"same(resolve_at({call}), ({r['index']}, "
                  f"{literal(r['confidence'])}))")
        return self.carrier_tuple((r["index"], r["confidence"]))

    def b_agree_at(self, *args):
        if len(args) < 2:
            raise self.error("TypeError", "agree_at() needs a rate and at "
                                          "least one read")
        rate = self._rate_arg(args[0], "agree_at")
        reads = [self._mask_arg(x) for x in args[1:]]
        r = ps.agree_at(rate, reads)
        call = ", ".join([literal(rate)] + [str(x) for x in reads])
        language, math = self._agree_language(r, reads, rate)
        self.step("substrate", language, math,
                  f"same(agree_at({call}), ({r['value']}, "
                  f"{literal(r['confidence'])}))")
        return self.carrier_tuple((r["value"], r["confidence"]))

    def b_resolve_floor(self, *args):
        if len(args) < 4:
            raise self.error("TypeError", "resolve_floor() needs a rate, a "
                                          "floor, a subject and at least one "
                                          "case")
        rate = self._rate_arg(args[0], "resolve_floor")
        floor = self._rate_arg(args[1], "resolve_floor")
        subject = self._mask_arg(args[2])
        cases = [self._mask_arg(c) for c in args[3:]]
        at = ", ".join([literal(rate)] + [str(x) for x in [subject] + cases])
        call = ", ".join([literal(rate), literal(floor)]
                         + [str(x) for x in [subject] + cases])
        try:
            r = ps.resolve_floor(rate, floor, subject, cases)
        except PythonRefusal as exc:
            self._floor_refusal(exc, f"resolve_at({at})[1] < {literal(floor)}")
        language, math = self._resolve_language(r, rate)
        self.step("substrate", language[:-1] + f", at or above the declared "
                  f"floor {floor}.", math + f" ≥ {floor}",
                  f"same(resolve_floor({call}), {r['index']})")
        return r["index"]

    def b_agree_floor(self, *args):
        if len(args) < 3:
            raise self.error("TypeError", "agree_floor() needs a rate, a "
                                          "floor and at least one read")
        rate = self._rate_arg(args[0], "agree_floor")
        floor = self._rate_arg(args[1], "agree_floor")
        reads = [self._mask_arg(x) for x in args[2:]]
        at = ", ".join([literal(rate)] + [str(x) for x in reads])
        call = ", ".join([literal(rate), literal(floor)]
                         + [str(x) for x in reads])
        try:
            r = ps.agree_floor(rate, floor, reads)
        except PythonRefusal as exc:
            self._floor_refusal(exc, f"agree_at({at})[1] < {literal(floor)}")
        language, math = self._agree_language(r, reads, rate)
        self.step("substrate", language[:-1] + f", at or above the declared "
                  f"floor {floor}.", math + f" ≥ {floor}",
                  f"same(agree_floor({call}), {r['value']})")
        return r["value"]

    # -- the rate posterior (studies/RATE_POSTERIOR_STUDY.md) ----------------
    def _soft_language(self, r, what: str) -> Tuple[str, str]:
        post = ", ".join(f"{p}: {_decimal7(x)}"
                         for p, x in zip(ps.SOFT_GRID, r["posterior"]))
        language = (f"{what}; read the bit-flip rate off the call's own "
                    f"{r['reads']} read(s) over the declared grid (uniform "
                    f"prior; most probable {', '.join(str(p) for p in r['most_probable'])}), "
                    f"and weigh the confidence at each rate by its posterior: "
                    f"{r['value']:#x} is the one sent with marginal probability "
                    f"{_decimal7(r['confidence'])} — {r['band']}.")
        math = (f"P(p | reads) ∝ Π_obs (1/4096) Σ_c p^D(c) q^(n−D(c)) = "
                f"{{{post}}}; Σ_p P(p | reads) · P(c | reads, p) = "
                f"{r['confidence']}")
        return language, math

    def b_decode_soft(self, *args):
        if len(args) < 1:
            raise self.error("TypeError", "decode_soft() needs a subject")
        reads = [self._mask_arg(x) for x in args]
        r = ps.decode_soft(reads[0], reads[1:])
        call = ", ".join(str(x) for x in reads)
        language, math = self._soft_language(
            r, f"Decode the subject (coset weight {r['coset_weight']})")
        self.step("substrate", language, math,
                  f"same(decode_soft({call}), ({r['value']}, "
                  f"{literal(r['confidence'])}))")
        return self.carrier_tuple((r["value"], r["confidence"]))

    def b_decode_soft_floor(self, *args):
        if len(args) < 2:
            raise self.error("TypeError", "decode_soft_floor() needs a floor "
                                          "and a subject")
        floor = self._rate_arg(args[0], "decode_soft_floor")
        reads = [self._mask_arg(x) for x in args[1:]]
        at = ", ".join(str(x) for x in reads)
        call = ", ".join([literal(floor)] + [str(x) for x in reads])
        try:
            r = ps.decode_soft_floor(floor, reads[0], reads[1:])
        except PythonRefusal as exc:
            self._floor_refusal(exc, f"decode_soft({at})[1] < {literal(floor)}")
        language, math = self._soft_language(
            r, f"Decode the subject (coset weight {r['coset_weight']})")
        self.step("substrate", language[:-1] + f", at or above the declared "
                  f"floor {floor}.", math + f" ≥ {floor}",
                  f"same(decode_soft_floor({call}), {r['value']})")
        return r["value"]

    def b_agree_soft(self, *args):
        if len(args) < 2:
            raise self.error("TypeError", "agree_soft() needs two reads of one "
                                          "carrier")
        reads = [self._mask_arg(x) for x in args]
        r = ps.agree_soft(reads[0], reads[1], reads[2:])
        call = ", ".join(str(x) for x in reads)
        language, math = self._soft_language(
            r, "Carry the forks of the two reads of one carrier and keep the "
               "one codeword both allow")
        self.step("substrate", language, math,
                  f"same(agree_soft({call}), ({r['value']}, "
                  f"{literal(r['confidence'])}))")
        return self.carrier_tuple((r["value"], r["confidence"]))

    def b_ds_bits(self, *args):
        self._need(args, 2, 2, "ds_bits")
        t, n = args
        if not _is_num(t) or not _is_int(n):
            raise self.error("TypeError", "ds_bits(t, n) takes a rational "
                                          "and an int")
        self.tick(int(n))
        value = ps.ds_bits(t, int(n))
        self.carrier_tuple(value)
        ones = sum(value)
        self.step("integer", f"Run the delta-sigma loop for {n} ticks of the "
                  f"generator on input {_m(t)}.",
                  f"bits = {''.join(map(str, value))}; Σ bits = {ones} = "
                  f"⌊{n}·{_m(Fraction(t))}⌋",
                  f"same(ds_bits({literal(t)}, {n}), {literal(value)})")
        return value

    def b_plane(self, *args):
        self._need(args, 2, 2, "plane")
        q, k = args
        if not _is_num(q) or not _is_int(k):
            raise self.error("TypeError", "plane(q, k) takes a rational and "
                                          "an int")
        value = ps.plane(q, int(k))
        self.step("integer", f"Read {_m(q)} at plane {k} of the dyadic "
                  "tower.", f"⌊{_m(Fraction(q))} · 2^{k}⌋ = {value}",
                  f"same(plane({literal(q)}, {k}), {value})")
        return value


# ===========================================================================
# 4.  THE PAYLOAD
# ===========================================================================

@dataclass
class SpeechPayload:
    """A Three Column Thinking payload for one program."""

    source: str
    answered: bool
    value: object = None
    value_literal: Optional[str] = None
    refusal: Optional[str] = None
    reason: Optional[str] = None
    certificate: Optional[str] = None
    error_class: Optional[str] = None
    steps: List[Step] = field(default_factory=list)
    cost: int = 0
    address: Optional[Dict[str, object]] = None
    column1: List[str] = field(default_factory=list)
    column2: List[str] = field(default_factory=list)
    column3: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {"source": self.source, "answered": self.answered,
                "value": self.value_literal, "refusal": self.refusal,
                "reason": self.reason, "steps": len(self.steps),
                "cost": self.cost, "column1_language": self.column1,
                "column2_mathematics": self.column2,
                "column3_script": self.column3}


def _carrier_line(v) -> Optional[str]:
    if _is_num(v) and not isinstance(v, bool):
        return f"carrier: q_0 = {_m(v)}, q_1 … q_23 = 0"
    if isinstance(v, bool):
        return f"substrate: one F₂ bit = {1 if v else 0}"
    if isinstance(v, tuple) and all(_is_num(x) for x in v):
        return ("carrier: (" + ", ".join(_m(Fraction(x)) for x in v)
                + ", 0" * (ps.WIDTH - len(v)) + ")" if len(v) < ps.WIDTH
                else ")")
    if isinstance(v, str):
        pts = [ord(c) for c in v[:8]]
        return (f"carrier(s): {-(-len(v) // ps.WIDTH)} × 24 code points; "
                f"first {pts}")
    if isinstance(v, frozenset):
        return f"mask: {ps.mask_of_frozenset(v):#026b}"
    return None


def speak(source: str, max_steps: int = MAX_STEPS) -> SpeechPayload:
    """Evaluate ``source`` and build its three columns."""
    ev = Evaluator(max_steps=max_steps)
    payload = SpeechPayload(source=source, answered=False)
    try:
        value = ev.run(source)
        payload.answered = True
        payload.value = value
        payload.value_literal = literal(value)
    except PythonRefusal as r:
        payload.refusal, payload.reason = r.name, r.reason
        payload.certificate = ev.certificate
        payload.error_class = ev.error_class
    except (_Return, _Break, _Continue):
        payload.refusal, payload.reason = "UNSUPPORTED", "control flow " \
                                                         "outside its block"
    except RecursionError:
        payload.refusal, payload.reason = "BUDGET", "nesting too deep"
    except SyntaxError as exc:
        payload.refusal, payload.reason = "PYTHON_ERROR", f"SyntaxError: {exc}"
        payload.error_class = "SyntaxError"
    payload.steps, payload.cost = list(ev.steps), ev.cost
    try:
        tree = ast.parse(source)
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            payload.address = ps.ast_address(ast.unparse(tree.body[-1].value))
    except SyntaxError:
        payload.address = None
    payload.column1, payload.column2 = _columns(payload)
    payload.column3 = render_script(payload)
    return payload


def _columns(p: SpeechPayload) -> Tuple[List[str], List[str]]:
    c1, c2 = [], []
    for i, s in enumerate(p.steps, 1):
        c1.append(f"{i}. [{s.layer}] {s.language}")
        c2.append(f"{i}. {s.math}")
    if p.answered:
        c1.append(f"Result: {p.value_literal}.")
        line = _carrier_line(p.value)
        c2.append(f"value = {p.value_literal}" + (f"; {line}" if line else ""))
    else:
        c1.append(f"Refused ({p.refusal}): {p.reason}.")
        c2.append(f"REFUSAL {p.refusal}" + (f"; certificate: {p.certificate}"
                                             if p.certificate else ""))
    if p.address is not None:
        addr = p.address
        c2.append(f"AST address: {addr['nodes']} nodes, {addr['dag_nodes']} "
                  f"DAG nodes, depth {addr['depth']}")
    return c1, c2


# ===========================================================================
# 5.  COLUMN 3
# ===========================================================================

_SCRIPT_HEAD = '''"""Column 3 of a Three Column Thinking payload -- generated.

Re-derives every step of column 2 with CPython's own operators, then re-runs
the whole program under CPython with the plain-Python prelude. Prints
VERIFIED True only if every check passes; exits 1 otherwise.
"""

import sys
'''

_SCRIPT_CHECK = '''

SOURCE = %(source)r
_passed = 0


def check(n, ok):
    global _passed
    if ok is not True:
        print("FAILED check %%d" %% n)
        sys.exit(1)
    _passed += 1

'''


def render_script(p: SpeechPayload, claimed: Optional[str] = None) -> str:
    """The column-3 script; ``claimed`` overrides the final claim."""
    lines = [_SCRIPT_HEAD, ps.PRELUDE, _SCRIPT_CHECK % {"source": p.source}]
    n = 0
    for s in p.steps:
        n += 1
        lines.append(f"check({n}, {s.check})")
    if p.answered:
        n += 1
        lines.append(f"check({n}, same(run_source(SOURCE), "
                     f"{claimed if claimed is not None else p.value_literal}))")
    else:
        if p.certificate:
            n += 1
            lines.append(f"check({n}, bool({p.certificate}))")
        if p.refusal in ("AMBIGUOUS", "UNCORRECTABLE", "SCALE_MISMATCH"):
            n += 1
            lines.append("try:\n    run_source(SOURCE)\n    _raised = None\n"
                         "except GLMRefusal as _r:\n    _raised = _r.name")
            lines.append(f"check({n}, _raised == {p.refusal!r})")
        elif p.refusal == "PYTHON_ERROR" and p.error_class:
            n += 1
            lines.append("try:\n    run_source(SOURCE)\n    _raised = None\n"
                         "except Exception as _e:\n"
                         "    _raised = type(_e).__name__")
            lines.append(f"check({n}, _raised == {p.error_class!r})")
    lines.append('print("checks re-derived:", _passed)')
    lines.append('print("VERIFIED True")')
    return "\n".join(lines) + "\n"


def mutated_script(p: SpeechPayload) -> str:
    """The same script with the final claim changed: it must fail."""
    v = p.value
    if isinstance(v, bool):
        claim = repr(not v)
    elif isinstance(v, (int, Fraction)):
        claim = literal(v + 1)
    elif isinstance(v, str):
        claim = repr(v + "!")
    elif isinstance(v, tuple):
        claim = literal(v + (0,))
    elif isinstance(v, frozenset):
        claim = literal(v ^ frozenset({0}))
    else:
        claim = f"({p.value_literal},)"
    return render_script(p, claimed=claim)


def verify_payload(p: SpeechPayload, script: Optional[str] = None,
                   timeout: int = 120) -> Dict[str, object]:
    """Run column 3 with ``python3 -I`` in a fresh process."""
    from ..runtime.python_tct import run_column3
    return run_column3(p.column3 if script is None else script, timeout)


# ===========================================================================
# 6.  THE MEASUREMENT (studies/PYTHON_SPEECH_STUDY.md §2)
# ===========================================================================

def _cpython_reference(source: str):
    ns: Dict[str, object] = {}
    exec(ps.PRELUDE, ns)
    value = ns["run_source"](source)
    return ns, value


#: The operand atoms of the differential battery (declared after P1-P6,
#: so it is reported as a post-hoc probe, not as a pass mark).
BATTERY_ATOMS: Tuple[str, ...] = (
    "0", "1", "-3", "7", "True", "False", "Fraction(2, 3)", "Fraction(-5, 4)",
    "'ab'", "'xyz'", "(1, 2)", "()", "frozenset({1, 4})", "frozenset()",
    "range(0, 10, 3)", "None", "2**30", "-(2**40)",
)
BATTERY_OPERATORS: Tuple[str, ...] = (
    "+", "-", "*", "//", "%", "**", "<<", ">>", "&", "|", "^", "==", "!=",
    "<", "<=", ">", ">=", "in", "not in", "and", "or", "/",
)


def differential_battery() -> Dict[str, object]:
    """Every ``(a) op (b)`` over the battery atoms, against CPython.

    ``wrong`` counts answers that differ from CPython in type or value, or
    answers where CPython raises. A refusal is never wrong; it is split
    into CPython-also-raises (``PYTHON_ERROR`` with the same exception
    class), float or complex results (``FLOAT``), budget refusals (not run
    under CPython, whose run would be the expensive thing refused), and the
    rest, which are answers CPython gives and the dialect declines.
    """
    from itertools import product
    ns: Dict[str, object] = {}
    exec(ps.PRELUDE, ns)
    counts = {"total": 0, "answered": 0, "wrong": 0, "same_error": 0,
              "float_or_complex": 0, "budget": 0, "declined": 0,
              "error_class_differs": 0}
    declined: List[Tuple[str, str]] = []
    for a, b in product(BATTERY_ATOMS, repeat=2):
        for op in BATTERY_OPERATORS:
            src = f"({a}) {op} ({b})"
            counts["total"] += 1
            p = speak(src)
            if p.refusal == "BUDGET":
                counts["budget"] += 1
                continue
            try:
                ref, err = ns["run_source"](src), None
            except Exception as exc:                # noqa: BLE001
                ref, err = None, type(exc).__name__
            if p.answered:
                counts["answered"] += 1
                if err is not None or not ns["same"](
                        eval(p.value_literal, ns), ref):
                    counts["wrong"] += 1
            elif err is not None:
                if p.refusal == "PYTHON_ERROR" and p.error_class == err:
                    counts["same_error"] += 1
                else:
                    counts["error_class_differs"] += 1
            elif p.refusal == "FLOAT" and type(ref).__name__ in (
                    "float", "complex"):
                counts["float_or_complex"] += 1
            else:
                counts["declined"] += 1
                declined.append((src, p.refusal))
    counts["declined_examples"] = declined[:12]
    return counts


def question_surface_control() -> Dict[str, object]:
    """The value programs put to ``GLM.py -q`` (planner, then grammar).

    The control of ``studies/PYTHON_SPEECH_STUDY.md`` §4: how many of the
    declared value programs the pre-existing question surface solves.
    Minutes, not seconds; it is not part of the unit tests.
    """
    from ..runtime.python_tct import question_surface_control as run
    return run()


def python_speech_report(run_scripts: bool = True) -> Dict[str, object]:
    """P1-P6 against the pass marks declared before this module existed."""
    from ..evaluation import python_speech_cases as C
    from ..substrate import golay_decode as gd
    from itertools import combinations

    # P1 and P3 --------------------------------------------------------------
    p1_right, p1_wrong, p1_refused, p1_rows = 0, 0, 0, []
    p3_verified, p3_mutants_caught, p3_exact = 0, 0, 0
    for cid, src in C.VALUE_CASES:
        p = speak(src)
        ns, ref = _cpython_reference(src)
        if not p.answered:
            p1_refused += 1
            p1_rows.append((cid, "refused", p.refusal, p.reason))
            continue
        ok = ns["same"](eval(p.value_literal, ns), ref)
        p1_right += ok
        p1_wrong += not ok
        row = [cid, "right" if ok else "WRONG", p.value_literal, len(p.steps)]
        if run_scripts:
            v = verify_payload(p)
            m = verify_payload(p, mutated_script(p))
            p3_verified += v["verified"]
            p3_exact += v["exact"]
            p3_mutants_caught += not m["verified"]
            row += [v["verified"], not m["verified"]]
        p1_rows.append(tuple(row))

    # P2 ---------------------------------------------------------------------
    p2_right, p2_rows, p2_scripts = 0, [], 0
    for cid, src, want in C.REFUSAL_CASES:
        p = speak(src)
        got = p.refusal if not p.answered else "answered"
        p2_right += got == want
        row = [cid, want, got]
        if run_scripts and not p.answered:
            v = verify_payload(p)
            p2_scripts += v["verified"]
            row.append(v["verified"])
        p2_rows.append(tuple(row))

    # P4 ---------------------------------------------------------------------
    table = ps.lane_table()
    lanes_ok = all(r["computes"] and r["bijective"] and r["restores"]
                   for r in table.values())
    pairs_ok, pairs_total = 0, 0
    for a, b in C.BITWISE_OPERANDS:
        for op, want in (("and", a & b), ("or", a | b), ("xor", a ^ b),
                         ("andnot", a & ~b), ("not", ~a)):
            pairs_total += 1
            pairs_ok += ps.register_bitwise(op, a, b).value == want

    # P5 ---------------------------------------------------------------------
    c1, c2 = ps.golay_encode(1), ps.golay_encode(2)
    ball = branch_ok = ambiguous_ok = wrong = 0
    for w in range(5):
        for pos in combinations(range(24), w):
            e = sum(1 << i for i in pos)
            ball += 1
            c = ps.classify(c1 ^ e, [c1, c2])
            if w <= 3:
                if c.verdict == "branch" and c.branch == 0:
                    branch_ok += 1
                else:
                    wrong += 1
            else:
                if c.verdict == "AMBIGUOUS" and len(c.candidates) == 6 \
                        and c.coset_weight == 4:
                    ambiguous_ok += 1
                else:
                    wrong += 1

    # P6 ---------------------------------------------------------------------
    eq_ok = sum(ps.ast_address(a)["carrier"] == ps.ast_address(b)["carrier"]
                and ps.canonical_form(a) == ps.canonical_form(b)
                for a, b in C.EQUIVALENT_PAIRS)
    carriers = [ps.ast_address(s)["carrier"] for s in C.DISTINCT_EXPRESSIONS]
    forms = [ps.canonical_form(s) for s in C.DISTINCT_EXPRESSIONS]
    collisions = [(C.DISTINCT_EXPRESSIONS[i], C.DISTINCT_EXPRESSIONS[j])
                  for i, j in combinations(range(len(carriers)), 2)
                  if carriers[i] == carriers[j]]
    form_collisions = [(C.DISTINCT_EXPRESSIONS[i], C.DISTINCT_EXPRESSIONS[j])
                       for i, j in combinations(range(len(forms)), 2)
                       if forms[i] == forms[j]]

    nv, nr = len(C.VALUE_CASES), len(C.REFUSAL_CASES)
    marks = {
        "P1": {"passed": p1_right == nv and p1_wrong == 0,
               "right": p1_right, "wrong": p1_wrong, "refused": p1_refused,
               "of": nv, "faculty": "derive"},
        "P2": {"passed": p2_right == nr, "right": p2_right, "of": nr,
               "refusal_scripts_verified": p2_scripts, "faculty": "refuse"},
        "P3": {"passed": (not run_scripts) or (p3_verified == p1_right
                                               and p3_mutants_caught
                                               == p1_right),
               "verified": p3_verified, "exact": p3_exact,
               "mutants_caught": p3_mutants_caught, "of": p1_right,
               "ran": run_scripts, "faculty": "derive"},
        "P4": {"passed": lanes_ok and pairs_ok == pairs_total,
               "programs": table, "pairs_right": pairs_ok,
               "pairs": pairs_total, "faculty": "derive"},
        "P5": {"passed": wrong == 0 and ball == 12951, "ball": ball,
               "branched": branch_ok, "ambiguous": ambiguous_ok,
               "wrong": wrong, "faculty": "refuse"},
        "P6": {"passed": eq_ok == len(C.EQUIVALENT_PAIRS) and not collisions,
               "equivalent_shared": eq_ok, "equivalent": len(
                   C.EQUIVALENT_PAIRS), "distinct": len(
                   C.DISTINCT_EXPRESSIONS), "collisions": collisions,
               "form_collisions": form_collisions, "faculty": "address"},
    }
    return {"marks": marks, "value_rows": p1_rows, "refusal_rows": p2_rows,
            "covering_radius": gd.COVERING_RADIUS,
            "met": sorted(k for k, v in marks.items() if v["passed"]),
            "not_met": sorted(k for k, v in marks.items() if not v["passed"])}
