"""``glm_universal.reasoning.python_containers`` -- the dialect widened (Phase 94).

``studies/THIRD_SORT_STUDY.md`` §2.2, candidate I1 of the order of work.  The
Phase 64 dialect refused every list and dict (``MUTABLE_CONTAINER``) and every
string method (``UNSUPPORTED``).  This module holds what admits them, as
functions of the running :class:`~glm_universal.reasoning.python_speech.
Evaluator`, so that every operation still records its step with a check
CPython re-derives in column 3:

* **String methods over code points.** ``find``, ``index``, ``count``,
  ``startswith``, ``endswith``, ``replace``, ``split`` with a separator,
  ``join`` and the ``strip`` family with characters are computed here by
  scanning code points.  ``upper``, ``lower``, ``isdigit``, ``isalpha`` and
  ``split`` / ``strip`` without arguments read Unicode's case and whitespace
  tables, which the substrate does not hold: they are computed by code-point
  arithmetic over ASCII and refused ``OUTSIDE_SUBSTRATE`` on a string with any
  code point above 127.
* **Lists and dicts as immutable snapshots.** A list or a dict is a value,
  never a place.  Every method that would change one, an item assignment and
  an augmented assignment to a name holding one (CPython performs it in
  place, visible through every alias) are refused ``MUTABLE_CONTAINER``.  A
  list holds at most 24 entries, as a tuple does.  Dict keys are compared by
  the evaluator's own exact equality, so ``1``, ``True`` and ``Fraction(1)``
  are one key, as in CPython, and the first key written is kept.
* **Dict views** (``keys``, ``values``, ``items``) are admitted where they are
  consumed and refused as a final value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from . import python_substrate as ps
from .python_substrate import PythonRefusal

__all__ = ["View", "ASCII_WHITESPACE", "str_method", "list_method",
           "dict_method", "build_dict", "dict_lookup", "carrier_list",
           "STR_METHODS", "LIST_MUTATORS", "DICT_MUTATORS", "hashable",
           "ascii_upper", "ascii_lower"]

#: The code points CPython's argument-free ``split`` and ``strip`` treat as
#: whitespace below 128.
ASCII_WHITESPACE = frozenset({9, 10, 11, 12, 13, 28, 29, 30, 31, 32})

STR_METHODS = ("upper", "lower", "find", "index", "count", "startswith",
               "endswith", "replace", "split", "join", "strip", "lstrip",
               "rstrip", "isdigit", "isalpha")
LIST_METHODS = ("index", "count")
LIST_MUTATORS = ("append", "extend", "insert", "pop", "remove", "sort",
                 "reverse", "clear")
DICT_METHODS = ("get", "keys", "values", "items")
DICT_MUTATORS = ("update", "pop", "popitem", "setdefault", "clear")


@dataclass(frozen=True)
class View:
    """A dict view: ``kind`` is ``keys``, ``values`` or ``items``."""

    kind: str
    pairs: Tuple[Tuple[object, object], ...]

    def items_(self) -> list:
        if self.kind == "keys":
            return [k for k, _ in self.pairs]
        if self.kind == "values":
            return [v for _, v in self.pairs]
        return [(k, v) for k, v in self.pairs]


def _lit(v) -> str:
    from .python_speech import literal
    return literal(v)


def _cps(s: str) -> List[int]:
    return [ord(c) for c in s]


def _is_ascii(s: str) -> bool:
    return all(ord(c) < 128 for c in s)


def ascii_upper(s: str) -> str:
    return "".join(chr(ord(c) - 32) if 97 <= ord(c) <= 122 else c for c in s)


def ascii_lower(s: str) -> str:
    return "".join(chr(ord(c) + 32) if 65 <= ord(c) <= 90 else c for c in s)


def _find(hay: List[int], needle: List[int], start: int = 0) -> int:
    n, m = len(hay), len(needle)
    for i in range(start, n - m + 1):
        if hay[i:i + m] == needle:
            return i
    return -1


def _occurrences(hay: List[int], needle: List[int]) -> List[int]:
    """Left-to-right non-overlapping occurrences of a non-empty needle."""
    out, i = [], 0
    while True:
        j = _find(hay, needle, i)
        if j < 0:
            return out
        out.append(j)
        i = j + len(needle)


def carrier_list(items) -> list:
    if len(items) > ps.WIDTH:
        raise PythonRefusal("CARRIER_OVERFLOW", f"a list of {len(items)} does "
                            "not fit one 24-coordinate carrier")
    return list(items)


def _need_str(ev, x, what: str) -> str:
    if not isinstance(x, str):
        raise ev.error("TypeError", f"{what} must be str, not "
                       f"{type(x).__name__}")
    return x


def _outside(name: str) -> PythonRefusal:
    return PythonRefusal("OUTSIDE_SUBSTRATE", f"str.{name} reads Unicode's "
                         "case or whitespace tables, which the substrate does "
                         "not hold; it is computed only over ASCII")


def str_method(ev, attr: str, s: str, args: list):
    """One string method, computed over code points, with its step."""
    call = f"{_lit(s)}.{attr}({', '.join(_lit(a) for a in args)})"

    def done(value, math: str):
        ev.tick(max(len(s), 1))
        ev.step("rational", f"str.{attr} over {len(s)} code points.", math,
                f"same({call}, {_lit(value)})")
        return value

    def arity(lo: int, hi: int) -> None:
        if not lo <= len(args) <= hi:
            raise PythonRefusal("UNSUPPORTED", f"str.{attr} with {len(args)} "
                                "arguments (start, end and count arguments "
                                "are not admitted)")
    if attr in ("upper", "lower", "isdigit", "isalpha"):
        arity(0, 0)
        if not _is_ascii(s):
            raise _outside(attr)
        if attr == "upper":
            return done(ascii_upper(s), "c ↦ c − 32 on 97…122")
        if attr == "lower":
            return done(ascii_lower(s), "c ↦ c + 32 on 65…90")
        if attr == "isdigit":
            v = bool(s) and all(48 <= ord(c) <= 57 for c in s)
            return done(v, "every c ∈ 48…57, and at least one")
        v = bool(s) and all(65 <= ord(c) <= 90 or 97 <= ord(c) <= 122
                            for c in s)
        return done(v, "every c ∈ 65…90 ∪ 97…122, and at least one")
    if attr in ("find", "index", "count", "startswith", "endswith"):
        arity(1, 1)
        sub = _need_str(ev, args[0], f"str.{attr}'s argument")
        hay, nd = _cps(s), _cps(sub)
        if attr in ("find", "index"):
            i = _find(hay, nd)
            if i < 0 and attr == "index":
                raise ev.error("ValueError", "substring not found")
            return done(i, f"least i with s[i : i + {len(nd)}] = needle, "
                           f"else −1: {i}")
        if attr == "count":
            v = len(hay) + 1 if not nd else len(_occurrences(hay, nd))
            return done(v, f"non-overlapping occurrences: {v}")
        if attr == "startswith":
            return done(hay[:len(nd)] == nd, "s[0 : |p|] = p")
        return done(len(nd) <= len(hay) and hay[len(hay) - len(nd):] == nd,
                    "s[|s| − |p| : |s|] = p")
    if attr == "replace":
        arity(2, 2)
        old = _need_str(ev, args[0], "replace's first argument")
        new = _need_str(ev, args[1], "replace's second argument")
        if not old:
            v = new + "".join(c + new for c in s)
        else:
            hay, nd = _cps(s), _cps(old)
            out, i = [], 0
            for j in _occurrences(hay, nd):
                out.append(s[i:j])
                out.append(new)
                i = j + len(nd)
            out.append(s[i:])
            v = "".join(out)
        return done(v, f"left-to-right non-overlapping replacement: "
                       f"{len(s)} → {len(v)} code points")
    if attr == "split":
        arity(0, 1)
        if not args or args[0] is None:
            if not _is_ascii(s):
                raise _outside("split")
            parts, cur = [], []
            for c in s:
                if ord(c) in ASCII_WHITESPACE:
                    if cur:
                        parts.append("".join(cur))
                        cur = []
                else:
                    cur.append(c)
            if cur:
                parts.append("".join(cur))
            return done(carrier_list(parts), f"maximal runs of non-whitespace:"
                                             f" {len(parts)} fields")
        sep = _need_str(ev, args[0], "split's separator")
        if not sep:
            raise ev.error("ValueError", "empty separator")
        parts, i = [], 0
        for j in _occurrences(_cps(s), _cps(sep)):
            parts.append(s[i:j])
            i = j + len(sep)
        parts.append(s[i:])
        return done(carrier_list(parts), f"cut at {len(parts) - 1} "
                                         "non-overlapping separators")
    if attr in ("strip", "lstrip", "rstrip"):
        arity(0, 1)
        if not args or args[0] is None:
            if not _is_ascii(s):
                raise _outside(attr)
            drop = ASCII_WHITESPACE
        else:
            drop = frozenset(_cps(_need_str(ev, args[0], f"{attr}'s "
                                                         "characters")))
        a, b = 0, len(s)
        if attr in ("strip", "lstrip"):
            while a < b and ord(s[a]) in drop:
                a += 1
        if attr in ("strip", "rstrip"):
            while b > a and ord(s[b - 1]) in drop:
                b -= 1
        return done(s[a:b], f"drop {a} code points before and {len(s) - b} "
                            "after")
    if attr == "join":
        arity(1, 1)
        items = list(ev.iterate(args[0]))
        for i, x in enumerate(items):
            if not isinstance(x, str):
                raise ev.error("TypeError", f"sequence item {i}: expected str "
                               f"instance, {type(x).__name__} found")
        out = []
        for i, x in enumerate(items):
            if i:
                out.append(s)
            out.append(x)
        v = "".join(out)
        return done(v, f"{len(items)} blocks with the separator between")
    raise PythonRefusal("UNSUPPORTED", f"attribute .{attr} of a str")


def list_method(ev, attr: str, xs: list, args: list):
    if attr in LIST_MUTATORS:
        raise PythonRefusal("MUTABLE_CONTAINER", f"list.{attr} would change "
                            "the list in place; build a new list instead")
    if attr not in LIST_METHODS or len(args) != 1:
        raise PythonRefusal("UNSUPPORTED", f"list.{attr} with {len(args)} "
                            "arguments")
    hits = [i for i, x in enumerate(xs) if ev.equal(args[0], x)]
    if attr == "index":
        if not hits:
            raise ev.error("ValueError", "value is not in list")
        value = hits[0]
    else:
        value = len(hits)
    ev.step("rational", f"list.{attr} by exact comparison.",
            f"{attr} = {value}", f"same({_lit(xs)}.{attr}({_lit(args[0])}), "
            f"{_lit(value)})")
    return value


def hashable(v) -> bool:
    if isinstance(v, (list, dict, View)):
        return False
    if isinstance(v, tuple):
        return all(hashable(x) for x in v)
    return True


def dict_lookup(ev, d: dict, key):
    """``(found, value)`` for ``key`` by the evaluator's exact equality."""
    if not hashable(key):
        raise ev.error("TypeError", f"unhashable type: "
                       f"'{type(key).__name__}'")
    for k, v in d.items():
        if ev.equal(k, key):
            return True, v
    return False, None


def build_dict(ev, pairs: list) -> dict:
    keys: list = []
    values: list = []
    for k, v in pairs:
        if not hashable(k):
            raise ev.error("TypeError", f"unhashable type: "
                           f"'{type(k).__name__}'")
        for i, k0 in enumerate(keys):
            if ev.equal(k0, k):
                values[i] = v
                break
        else:
            keys.append(k)
            values.append(v)
    if len(keys) > ps.WIDTH:
        raise PythonRefusal("CARRIER_OVERFLOW", f"a dict of {len(keys)} keys "
                            "does not fit one 24-coordinate carrier")
    value = dict(zip(keys, values))
    ev.step("rational", f"Lay {len(keys)} key-value pairs on the carrier, in "
            "insertion order, equal keys merged.",
            f"{{k_i ↦ v_i}}, |keys| = {len(keys)}",
            f"same({{{', '.join(_lit(k) + ': ' + _lit(v) for k, v in pairs)}}},"
            f" {_lit(value)})")
    return value


def dict_method(ev, attr: str, d: dict, args: list):
    if attr in DICT_MUTATORS:
        raise PythonRefusal("MUTABLE_CONTAINER", f"dict.{attr} would change "
                            "the dict in place; build a new dict instead")
    if attr in ("keys", "values", "items"):
        if args:
            raise ev.error("TypeError", f"dict.{attr}() takes no arguments")
        return View(attr, tuple(d.items()))
    if attr == "get" and 1 <= len(args) <= 2:
        found, v = dict_lookup(ev, d, args[0])
        value = v if found else (args[1] if len(args) == 2 else None)
        ev.step("rational", "Read a key, or the default.",
                f"get = {_lit(value)}",
                f"same({_lit(d)}.get({', '.join(_lit(a) for a in args)}), "
                f"{_lit(value)})")
        return value
    raise PythonRefusal("UNSUPPORTED", f"dict.{attr} with {len(args)} "
                        "arguments")
