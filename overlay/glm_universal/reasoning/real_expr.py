"""Written arithmetic over exact reals: ``sqrt(2) + pi/4``, and what it costs.

:mod:`~glm_universal.reasoning.exact_real` holds a real number as a *process*:
a rule that produces, for any precision asked of it, an exact rational within
that precision.  This module is the front door to it.  It reads an ordinary
written expression --

``sqrt(2) + sqrt(3)``, ``pi/4``, ``2*phi - 1``, ``root(3, 2)``, ``(1+sqrt(5))/2``

-- and returns the process the expression denotes.  No float is constructed at
any point, and nothing is rounded until a decimal readout is asked for.

What is deliberately *not* hidden
---------------------------------
Two things about real arithmetic cannot be made to work, and this module
declines to pretend otherwise.

**Division needs a witness.**  ``1/x`` is computable only from a bound
``|x| >= 2**-m``; no algorithm can produce that bound for an arbitrary
process, because doing so would decide whether the process is zero.  So the
parser *searches* for a witness up to a stated depth
(:data:`WITNESS_DEPTH`), and if the divisor has not moved away from zero by
then it raises :class:`~glm_universal.reasoning.exact_real.PrecisionError`
naming the depth reached.  That refusal is the honest answer, not a defect:
the divisor may be zero.

**Equality is not decidable.**  The parser will happily build
``sqrt(2)*sqrt(2) - 2``; asking whether it *is* zero is exactly the question
above, and :func:`~glm_universal.reasoning.exact_real.decide_equal` answers
``None``.

Grammar
-------
::

    expression := term (("+" | "-") term)*
    term       := unary (("*" | "/") unary)*
    unary      := ("+" | "-")* power
    power      := atom ("^" unary)?
    atom       := number | constant | function "(" arguments ")"
                | "(" expression ")"
    function   := "sqrt" | "cbrt" | "root"        # root(degree, x)
                | "exp" | "log" | "ln"            # log(x), log(base, x)
                | "sin" | "cos" | "tan"
    constant   := "pi" | "e" | "phi"
    number     := integer | integer "/" integer | decimal literal

An integer exponent is repeated multiplication (a negative one is a
reciprocal, and so needs the same witness a division does).  Any other
exponent goes through :func:`~glm_universal.reasoning.transcendental.rpow` --
``base ** exponent = exp(exponent * log base)`` -- so it needs the base to be
**positive**, and a base that has not moved above zero is refused with the
depth named, exactly as a divisor is.  ``2^(1/3)`` and ``root(3, 2)`` are the
same number by two routes, and both are available.

The transcendental functions are the ones
:mod:`~glm_universal.reasoning.transcendental` builds: ``exp``, the natural
logarithm (``log`` or ``ln``, and ``log(base, x)`` for another base), ``sin``,
``cos`` and ``tan``.  What is still refused by name is the *inverse*
trigonometric and hyperbolic family -- ``asin``, ``atan``, ``sinh`` and the
rest -- because none of them has been built yet.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

from .exact_real import (ExactReal, PrecisionError, e, from_fraction,
                         nonzero_witness, nth_root, phi, pi, sqrt)
from .transcendental import (POSITIVE_WITNESS_DEPTH, cos, exp, log,
                             positive_witness, rpow, sin, tan)

__all__ = [
    "WITNESS_DEPTH", "CONSTANTS", "FUNCTIONS", "UNBUILT_FUNCTIONS",
    "GRAMMAR_SUMMARY",
    "ExpressionError", "Token", "tokenise", "parse_expression",
    "divide", "power", "expression_report",
]


#: How far a divisor is refined in the search for a nonzero witness before the
#: division is refused.  Every rational and every algebraic constant this
#: module builds clears zero long before this; a difference that is *actually*
#: zero never will, which is the point.
WITNESS_DEPTH: int = 96

#: The named constants, each a process, not a stored decimal.
CONSTANTS: Tuple[str, ...] = ("pi", "e", "phi")

#: The functions, with the number of arguments each takes.  ``log`` takes one
#: argument (the natural logarithm) or two (``log(base, x)``), so it is listed
#: with the arity it is usually written at and handled explicitly.
FUNCTIONS: Tuple[Tuple[str, int], ...] = (
    ("sqrt", 1), ("cbrt", 1), ("root", 2),
    ("exp", 1), ("log", 1), ("ln", 1), ("sin", 1), ("cos", 1), ("tan", 1),
)

#: The functions that are refused by name rather than approximated.  Each
#: would need its own convergent process with a stated error bound, and none
#: is built; naming them is more useful than a generic "unknown function".
UNBUILT_FUNCTIONS: Tuple[str, ...] = (
    "asin", "acos", "atan", "arcsin", "arccos", "arctan",
    "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
    "erf", "gamma", "zeta",
)

GRAMMAR_SUMMARY: str = (
    "+ - * / ^, brackets, the constants pi, e, phi, "
    "sqrt(x), cbrt(x), root(<degree>, x), exp(x), log(x), log(<base>, x), "
    "ln(x), sin(x), cos(x), tan(x), and any rational or decimal literal"
)


class ExpressionError(ValueError):
    """The written expression is not one this module reads."""


# ===========================================================================
# 1.  TOKENS
# ===========================================================================

Token = Tuple[str, str]          # (kind, text)

_SYMBOLS = {"+": "op", "-": "op", "*": "op", "/": "op", "^": "op",
            "(": "open", ")": "close", ",": "comma"}


def tokenise(text: str) -> Tuple[Token, ...]:
    """Split a written expression into tokens.  Whitespace is not significant.

    Unicode ``π`` and ``φ`` are read as ``pi`` and ``phi``; everything else
    outside the grammar is an error naming the character that stopped it.
    """
    source = (str(text).strip().lower()
              .replace("π", "pi").replace("φ", "phi").replace("×", "*")
              .replace("−", "-").replace("÷", "/"))
    tokens: List[Token] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char.isspace():
            index += 1
            continue
        if char in _SYMBOLS:
            tokens.append((_SYMBOLS[char], char))
            index += 1
            continue
        if char.isdigit() or char == ".":
            start = index
            while index < len(source) and (source[index].isdigit()
                                           or source[index] == "."):
                index += 1
            tokens.append(("number", source[start:index]))
            continue
        if char.isalpha():
            start = index
            while index < len(source) and source[index].isalpha():
                index += 1
            tokens.append(("name", source[start:index]))
            continue
        raise ExpressionError(
            f"tokenise: {text!r} -- the character {char!r} at position "
            f"{index} is not part of the grammar; it reads {GRAMMAR_SUMMARY}")
    return tuple(tokens)


def _literal(text: str) -> Fraction:
    """A number token as an exact Fraction.  ``0.1`` is *one tenth*, exactly."""
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        raise ExpressionError(
            f"parse_expression: {text!r} is not a number literal") from None


# ===========================================================================
# 2.  THE OPERATIONS THAT NEED CARE
# ===========================================================================

def divide(numerator: ExactReal, denominator: ExactReal,
           depth: int = WITNESS_DEPTH) -> ExactReal:
    """``numerator / denominator``, refusing rather than guessing at zero.

    A rational denominator is divided out exactly.  Any other denominator
    needs a bound ``|d| >= 2**-m``; the bound is searched for to ``depth``
    and, if it is not found, the division is refused with the depth named.
    """
    if denominator.exact is not None:
        if denominator.exact == 0:
            raise ZeroDivisionError("divide: division by an exact zero")
        return numerator / denominator.exact
    witness = nonzero_witness(denominator, depth)
    if witness is None:
        raise PrecisionError(
            f"divide: the divisor {denominator.name} has not moved away from "
            f"zero by 2**-{depth}, so 1/{denominator.name} cannot be "
            f"computed -- the divisor may be zero, and no finite refinement "
            f"decides that")
    return numerator * denominator.reciprocal(witness)


def power(base: ExactReal, exponent: int,
          depth: int = WITNESS_DEPTH) -> ExactReal:
    """``base ** exponent`` for an integer exponent, by repeated product."""
    exponent = int(exponent)
    if exponent < 0:
        return divide(from_fraction(Fraction(1)),
                      power(base, -exponent, depth), depth)
    result = from_fraction(Fraction(1))
    for _ in range(exponent):
        result = result * base
    if exponent == 0:
        return from_fraction(Fraction(1))
    return ExactReal(result.approx, f"({base.name}^{exponent})",
                     result.exact)


# ===========================================================================
# 3.  THE PARSER
# ===========================================================================

class _Parser:
    """Recursive descent over the token stream.  No lookahead beyond one."""

    def __init__(self, tokens: Sequence[Token], source: str, depth: int):
        self.tokens = tuple(tokens)
        self.source = source
        self.depth = depth
        self.position = 0

    # -- token handling ----------------------------------------------------

    def peek(self) -> Optional[Token]:
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def take(self) -> Token:
        token = self.peek()
        if token is None:
            raise ExpressionError(
                f"parse_expression: {self.source!r} ends in the middle of an "
                f"expression")
        self.position += 1
        return token

    def expect(self, kind: str, text: Optional[str] = None) -> Token:
        token = self.take()
        if token[0] != kind or (text is not None and token[1] != text):
            wanted = text if text is not None else kind
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- expected {wanted!r}, "
                f"found {token[1]!r}")
        return token

    # -- grammar -----------------------------------------------------------

    def expression(self) -> ExactReal:
        value = self.term()
        while True:
            token = self.peek()
            if token is not None and token == ("op", "+"):
                self.take()
                value = value + self.term()
            elif token is not None and token == ("op", "-"):
                self.take()
                value = value - self.term()
            else:
                return value

    def term(self) -> ExactReal:
        value = self.unary()
        while True:
            token = self.peek()
            if token is not None and token == ("op", "*"):
                self.take()
                value = value * self.unary()
            elif token is not None and token == ("op", "/"):
                self.take()
                value = divide(value, self.unary(), self.depth)
            else:
                return value

    def unary(self) -> ExactReal:
        token = self.peek()
        if token == ("op", "-"):
            self.take()
            return -self.unary()
        if token == ("op", "+"):
            self.take()
            return self.unary()
        return self.power()

    def power(self) -> ExactReal:
        base = self.atom()
        token = self.peek()
        if token is not None and token == ("op", "^"):
            self.take()
            exponent = self.unary()          # right-associative, and may be
            if (exponent.exact is not None   # any expression at all
                    and exponent.exact.denominator == 1):
                return power(base, exponent.exact.numerator, self.depth)
            return self.real_power(base, exponent)
        return base

    def real_power(self, base: ExactReal, exponent: ExactReal) -> ExactReal:
        """``base ** exponent`` where the exponent is not an integer.

        This is ``exp(exponent * log base)``, which is what the power *is* for
        a positive base -- so a base that is not known to be positive is
        refused rather than guessed at, and a negative base has no real value
        here at all.
        """
        if base.exact is not None and base.exact < 0:
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- a negative base "
                f"({base.exact}) raised to a non-integer power has no real "
                f"value")
        try:
            return rpow(base, exponent, self.depth)
        except PrecisionError as error:
            raise PrecisionError(
                f"parse_expression: {self.source!r} -- {error}") from None
        except ValueError as error:
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- {error}") from None

    def atom(self) -> ExactReal:
        token = self.take()
        kind, text = token
        if kind == "open":
            value = self.expression()
            self.expect("close")
            return value
        if kind == "number":
            return from_fraction(_literal(text))
        if kind == "name":
            return self.named(text)
        raise ExpressionError(
            f"parse_expression: {self.source!r} -- {text!r} cannot start a "
            f"value; it reads {GRAMMAR_SUMMARY}")

    def named(self, text: str) -> ExactReal:
        if text == "pi":
            return pi()
        if text in ("e", "euler"):
            return e()
        if text in ("phi", "golden"):
            return phi()
        arities = dict(FUNCTIONS)
        if text in UNBUILT_FUNCTIONS:
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- {text!r} is not built: "
                f"it would need its own convergent process with a stated "
                f"error bound, and none is written.  What is built is "
                f"{GRAMMAR_SUMMARY}")
        if text not in arities:
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- {text!r} is not a "
                f"constant or function this module knows; it reads "
                f"{GRAMMAR_SUMMARY}")
        self.expect("open")
        arguments = [self.expression()]
        while self.peek() is not None and self.peek()[0] == "comma":
            self.take()
            arguments.append(self.expression())
        self.expect("close")
        if text in ("log", "ln"):
            return self.logarithm(text, arguments)
        if len(arguments) != arities[text]:
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- {text} takes "
                f"{arities[text]} argument(s), {len(arguments)} given")
        if text == "exp":
            return exp(arguments[0])
        if text == "sin":
            return sin(arguments[0])
        if text == "cos":
            return cos(arguments[0])
        if text == "tan":
            return self.tangent(arguments[0])
        if text == "sqrt":
            return self.checked_root(arguments[0], 2)
        if text == "cbrt":
            return self.checked_root(arguments[0], 3)
        degree, radicand = arguments
        if degree.exact is None or degree.exact.denominator != 1 or degree.exact < 1:
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- the degree of a root "
                f"must be a positive integer literal")
        return self.checked_root(radicand, int(degree.exact))

    def logarithm(self, spelling: str,
                  arguments: Sequence[ExactReal]) -> ExactReal:
        """``log(x)``, the natural logarithm, or ``log(base, x)``.

        Both routes need their arguments to be *positive*, and say so when
        they are not: producing the bound `x >= 2**-m` for an arbitrary
        process would decide whether the process is zero.
        """
        if len(arguments) == 1:
            return self.checked_log(arguments[0])
        if len(arguments) != 2:
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- {spelling} takes one "
                f"argument (the natural logarithm) or two, log(<base>, x)")
        base, value = arguments
        return divide(self.checked_log(value), self.checked_log(base),
                      self.depth)

    def checked_log(self, value: ExactReal) -> ExactReal:
        """A natural logarithm, with the refusals stated rather than hidden."""
        try:
            return log(value, None, self.depth)
        except PrecisionError as error:
            raise PrecisionError(
                f"parse_expression: {self.source!r} -- {error}") from None
        except ValueError as error:
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- {error}") from None

    def tangent(self, value: ExactReal) -> ExactReal:
        """``tan(x)``, refused where the cosine has not moved away from zero."""
        try:
            return tan(value, self.depth)
        except PrecisionError as error:
            raise PrecisionError(
                f"parse_expression: {self.source!r} -- {error}") from None

    def checked_root(self, radicand: ExactReal, degree: int) -> ExactReal:
        """A root, with the one case that has no real answer refused."""
        if radicand.exact is not None and radicand.exact < 0:
            raise ExpressionError(
                f"parse_expression: {self.source!r} -- root of the negative "
                f"number {radicand.exact}; this module builds real values "
                f"only")
        if radicand.exact is None:
            # A process may still be negative; the guard is the one the
            # constructor applies, and it is stated rather than hidden.
            probe = radicand.at(32)
            if probe < Fraction(-1, 2 ** 30):
                raise ExpressionError(
                    f"parse_expression: {self.source!r} -- the radicand "
                    f"{radicand.name} is negative ({probe} at 2**-32)")
        if degree == 2:
            return sqrt(radicand)
        return nth_root(radicand, degree)


def parse_expression(text: str, depth: int = WITNESS_DEPTH) -> ExactReal:
    """Read a written expression and return the process it denotes.

    >>> parse_expression("(1+sqrt(5))/2").decimal(10)
    '1.6180339887'
    """
    source = str(text).strip()
    if not source:
        raise ExpressionError("parse_expression: the expression is empty")
    parser = _Parser(tokenise(source), source, depth)
    value = parser.expression()
    leftover = parser.peek()
    if leftover is not None:
        raise ExpressionError(
            f"parse_expression: {source!r} -- {leftover[1]!r} is left over "
            f"after a complete expression")
    return ExactReal(value.approx, source, value.exact)


# ===========================================================================
# 4.  THE REPORT
# ===========================================================================

def expression_report() -> dict:
    """Recompute what this module claims, on demand.  Nothing here is quoted."""
    cases = (
        ("sqrt(2)+sqrt(3)", 20),
        ("(1+sqrt(5))/2", 20),
        ("pi/4", 20),
        ("root(3, 2)", 20),
        ("2^10", 0),
        ("1/3", 20),
        ("0.1+0.2", 20),
        ("exp(1)", 20),
        ("log(2)", 20),
        ("sin(1)", 20),
        ("cos(1)", 20),
        ("2^pi", 20),
        ("2^(1/3)", 20),
        ("log(2, 8)", 20),
    )
    values = tuple((text, parse_expression(text).decimal(places))
                   for text, places in cases)

    # The golden ratio two ways: the constant, and the expression for it.
    built = parse_expression("(1+sqrt(5))/2")
    same_to_60 = abs(built.at(60) - phi().at(60)) <= Fraction(1, 2 ** 58)

    # A cube root, checked against its own defining equation.
    cube = parse_expression("root(3, 2)")
    cube_residual = abs(cube.at(60) ** 3 - 2)

    # The refusals, each provoked here rather than described.
    refusals = {}
    for text in ("sqrt(2)/(sqrt(2)-sqrt(2))", "sqrt(-1)", "log(0)",
                 "log(1-1)", "(0-2)^pi", "asin(1)", "1+"):
        try:
            parse_expression(text, depth=24)
            refusals[text] = "accepted"
        except (ExpressionError, PrecisionError, ZeroDivisionError) as error:
            refusals[text] = f"{type(error).__name__}"

    # The transcendental layer, each value checked against an identity it
    # must satisfy rather than against a stored decimal.
    exp_log_round_trip = abs(parse_expression("exp(log(7/2))").at(60)
                             - Fraction(7, 2))
    pythagoras = abs(parse_expression("sin(1)^2+cos(1)^2").at(60) - 1)
    log_base_agrees = abs(parse_expression("log(2, 8)").at(60) - 3)
    power_is_the_root = abs(parse_expression("2^(1/3)").at(60)
                            - parse_expression("root(3, 2)").at(60))

    return {
        "grammar": GRAMMAR_SUMMARY,
        "witness_depth": WITNESS_DEPTH,
        "values": values,
        "phi_two_ways_agree": same_to_60,
        "cube_root_residual_below": cube_residual < Fraction(1, 2 ** 55),
        "cube_root_residual": str(cube_residual),
        "refusals": refusals,
        "decimal_literals_are_exact": (
            parse_expression("0.1+0.2").at(80) == Fraction(3, 10)),
        "unbuilt_functions": UNBUILT_FUNCTIONS,
        "exp_inverts_log": exp_log_round_trip <= Fraction(1, 2 ** 55),
        "pythagorean_identity": pythagoras <= Fraction(1, 2 ** 55),
        "log_base_8_of_2_is_3": log_base_agrees <= Fraction(1, 2 ** 55),
        "fractional_power_is_the_root": (
            power_is_the_root <= Fraction(1, 2 ** 55)),
    }
