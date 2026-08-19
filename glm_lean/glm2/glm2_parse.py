#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 PARSE  —  the expression language
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Layer  :  Tier 1c — surface syntax for meanings.
  Deps   :  glm2_meaning, glm2_library.

  Grammar (recursive descent, no dependencies, exact arithmetic throughout):

      expr    := term (('*' | '/') term)*
      term    := atom ('^' exponent)?
      atom    := NAME | CALL | NUMBER | '(' expr ')'
      CALL    := FUNC '(' expr (',' expr)* ')'
      exponent:= rational, optionally parenthesised and signed:
                 2, -3, (1/2), -(3/2), 0.5

  NAME resolves through the register (name, alias or symbol).

  CALL is how the tensor and differential structure is written.  Plain
  juxtaposition (`*`) is the TENSOR product, which adds ranks; the operations
  that do not are named functions:

      dot(a, b)        full contraction: rank(a) + rank(b) - 2
      cross(a, b)      plain cross product of two rank-1 quantities: rank 1,
                       parities add, no angle
      moment(a, b)     rotational cross product: as `cross`, with one extra
                       inverse radian (torque, angular momentum, omega x r)
      grad(x)          nabla tensor x: rank + 1, P flips, one inverse length
      div(x)           nabla dot x:    rank - 1, P flips, one inverse length
      curl(x)          nabla cross x:  rank 1, P flips, L^-1
      rot(x)           nabla moment x: rank 1, P flips, L^-1 A^-1
      laplacian(x)     div(grad(x)):   rank unchanged, L^-2, P unchanged
      ddt(x)           d/dt:           one inverse time (so T grading flips)
      integral_dt(x)   one extra time
      integral_dV(x)   three extra lengths

  So `dot(force, position)` is an energy while `force * position` is a rank-2
  tensor with the same dimensions, and GLM-2 keeps them apart.

  `cross` and `moment` are separated for a reason.  With the plane angle
  promoted to a dimension, the cross product that converts between rotation
  and translation consumes a radian (torque is joules per radian) and the one
  that does not (E x H) does not.  Keeping one operation for both is exactly
  the confusion that makes torque look like energy.  The same split appears
  one level up as `curl` (Maxwell) versus `rot` (vorticity).
  NUMBER must be a power of ten: it contributes only to the decimal scale, so
  "1000 * length" is a kilometre and "length / 1000" is a millimetre.  Any
  other numeric literal is refused rather than silently discarded, because a
  factor of 2 is not a dimensional statement and pretending otherwise is how
  unit bugs get in.

      python3 glm2_parse.py       # parser self-audit
================================================================================
"""

from __future__ import annotations

from fractions import Fraction as F
from typing import List, Optional, Tuple

from glm2_meaning import Meaning, ParseError, SCALAR
from glm2_library import resolve

__all__ = ["parse", "tokenise", "format_meaning", "FUNCTIONS", "NABLA"]


# ══════════════════════════════════════════════════════════════════════════════
# §0.  THE OPERATOR ALGEBRA
# ══════════════════════════════════════════════════════════════════════════════

#: the gradient operator, as a meaning in its own right: one inverse length,
#: rank 1, P-odd.  Every differential operator below is built from it, so
#: their rank and parity bookkeeping is forced rather than tabulated.
NABLA = Meaning.make(L=-1, rank=1, p=1)

#: one unit of time and one unit of volume, used by the integral operators
_TIME = Meaning.make(T=1)
_VOLUME = Meaning.make(L=3)


def _laplacian(x: Meaning) -> Meaning:
    return NABLA.contract(NABLA + x)


#: name -> (arity, implementation)
FUNCTIONS = {
    "dot":         (2, lambda a, b: a.contract(b)),
    "cross":       (2, lambda a, b: a.cross(b)),
    "moment":      (2, lambda a, b: a.moment(b)),
    "grad":        (1, lambda x: NABLA + x),
    "div":         (1, lambda x: NABLA.contract(x)),
    "curl":        (1, lambda x: NABLA.cross(x)),
    "rot":         (1, lambda x: NABLA.moment(x)),
    "laplacian":   (1, _laplacian),
    "ddt":         (1, lambda x: x - _TIME),
    "integral_dt": (1, lambda x: x + _TIME),
    "integral_dV": (1, lambda x: x + _VOLUME),
}


# ══════════════════════════════════════════════════════════════════════════════
# §1.  TOKENISER
# ══════════════════════════════════════════════════════════════════════════════

_PUNCT = set("*/^(),")


def tokenise(text: str) -> List[str]:
    out: List[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch in _PUNCT:
            out.append(ch)
            i += 1
            continue
        if ch == "-" or ch == "+":
            out.append(ch)
            i += 1
            continue
        if ch.isdigit() or ch == ".":
            j = i
            while j < n and (text[j].isdigit() or text[j] in ".eE"):
                if text[j] in "eE" and j + 1 < n and text[j + 1] in "+-":
                    j += 2
                    continue
                j += 1
            out.append(text[i:j])
            i = j
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] in "_"):
                j += 1
            out.append(text[i:j])
            i = j
            continue
        raise ParseError(f"unexpected character {ch!r} in {text!r}")
    return out


# ══════════════════════════════════════════════════════════════════════════════
# §2.  PARSER
# ══════════════════════════════════════════════════════════════════════════════

class _Parser:
    def __init__(self, tokens: List[str]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> str:
        tok = self.peek()
        if tok is None:
            raise ParseError("unexpected end of expression")
        self.pos += 1
        return tok

    def expect(self, tok: str) -> None:
        got = self.next()
        if got != tok:
            raise ParseError(f"expected {tok!r}, found {got!r}")

    # expr := term (('*'|'/') term)*
    def expr(self) -> Meaning:
        value = self.term()
        while self.peek() in ("*", "/"):
            op = self.next()
            rhs = self.term()
            value = value + rhs if op == "*" else value - rhs
        return value

    # term := atom ('^' exponent)?
    def term(self) -> Meaning:
        value = self.atom()
        while self.peek() == "^":
            self.next()
            value = value.power(self.exponent())
        return value

    def atom(self) -> Meaning:
        tok = self.next()
        if tok == "(":
            value = self.expr()
            self.expect(")")
            return value
        if tok == "-":
            raise ParseError("a leading minus is not a dimensional operation; "
                             "use an exponent such as ^-1")
        if tok[0].isdigit() or tok[0] == ".":
            return _numeric(tok)
        if tok in FUNCTIONS and self.peek() == "(":
            return self.call(tok)
        m = resolve(tok)
        if m is None:
            raise ParseError(f"unknown concept {tok!r}")
        return m

    def call(self, name: str) -> Meaning:
        arity, fn = FUNCTIONS[name]
        self.expect("(")
        args = [self.expr()]
        while self.peek() == ",":
            self.next()
            args.append(self.expr())
        self.expect(")")
        if len(args) != arity:
            raise ParseError(
                f"{name} takes {arity} argument(s), {len(args)} given")
        return fn(*args)

    def exponent(self) -> F:
        tok = self.next()
        sign = F(1)
        while tok in ("-", "+"):
            if tok == "-":
                sign = -sign
            tok = self.next()
        if tok == "(":
            value = self._rational_inside()
            self.expect(")")
            return sign * value
        return sign * _rational(tok)

    def _rational_inside(self) -> F:
        tok = self.next()
        sign = F(1)
        while tok in ("-", "+"):
            if tok == "-":
                sign = -sign
            tok = self.next()
        value = sign * _rational(tok)
        while self.peek() in ("/", "*"):
            op = self.next()
            nxt = self.next()
            s2 = F(1)
            while nxt in ("-", "+"):
                if nxt == "-":
                    s2 = -s2
                nxt = self.next()
            r = s2 * _rational(nxt)
            value = value / r if op == "/" else value * r
        return value


def _rational(tok: str) -> F:
    try:
        return F(tok)
    except (ValueError, ZeroDivisionError):
        raise ParseError(f"{tok!r} is not an exact rational exponent")


def _numeric(tok: str) -> Meaning:
    """A numeric literal: legal only when it is an exact power of ten."""
    try:
        value = F(tok)
    except ValueError:
        raise ParseError(f"{tok!r} is not a number")
    if value <= 0:
        raise ParseError(f"numeric factor {tok} must be positive")
    exponent = _power_of_ten(value)
    if exponent is None:
        raise ParseError(
            f"numeric factor {tok} is not a power of ten; GLM-2 tracks the "
            "decimal scale exactly and refuses to absorb other constants")
    return Meaning(SCALAR.exps, F(exponent))


def _power_of_ten(value: F) -> Optional[int]:
    if value == 1:
        return 0
    if value > 1:
        n = 0
        v = value
        while v % 10 == 0:
            v //= 10
            n += 1
        return n if v == 1 else None
    inv = 1 / value
    n = _power_of_ten(inv)
    return None if n is None else -n


def parse(text: str) -> Meaning:
    """Parse an expression into an exact Meaning."""
    tokens = tokenise(text)
    if not tokens:
        raise ParseError("empty expression")
    p = _Parser(tokens)
    value = p.expr()
    if p.peek() is not None:
        raise ParseError(f"trailing input at {p.peek()!r}")
    return value


def format_meaning(m: Meaning) -> str:
    return m.signature()


# ══════════════════════════════════════════════════════════════════════════════
# §3.  SELF-AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def _self_audit() -> List[Tuple[str, str]]:
    cases = [
        "mass * speed^2",
        "energy / (area * time)",
        "(energy / mass)^(1/2)",
        "length^(1/2) * stress",
        "1000 * length",
        "planck_constant / angle",
        "information / time",
        "dot(force, position)",
        "force * position",
        "moment(position, momentum)",
        "cross(electric_field, magnetic_field_h)",
        "grad(pressure)",
        "div(velocity)",
        "curl(magnetic_field_h)",
        "rot(velocity)",
        "laplacian(voltage)",
        "ddt(velocity)",
        "integral_dt(power)",
        "integral_dV(charge_density)",
    ]
    return [(c, str(parse(c))) for c in cases]


if __name__ == "__main__":  # pragma: no cover
    print("GLM-2 PARSE — self-audit")
    for text, value in _self_audit():
        print(f"  {text:34s} -> {value}")
    for bad in ["2 * length", "unknown_thing", "mass *", "length ^ x"]:
        try:
            parse(bad)
            print(f"  {bad:34s} -> ACCEPTED (should not be)")
        except ParseError as exc:
            print(f"  {bad:34s} -> refused: {exc}")
